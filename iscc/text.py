# -*- coding: utf-8 -*-
from loguru import logger
import unicodedata
from os.path import basename, splitext
from typing import Any, Generator, Union
from urllib.parse import urlparse
import langdetect
import xxhash
from functools import lru_cache
import langcodes
from iscc.schema import FeatureType
from iscc_core.cdc import data_chunks
from iscc.options import SdkOptions
from iscc import uread
from iscc.utils import sliding_window
from iscc_core.codec import encode_base64
from iscc.schema import Readable
from iscc.mediatype import mime_clean, mime_to_gmt
from iscc_core.minhash import minhash_64, minhash_256
from tika import parser as tika_parser


# Set for deterministic language detection
langdetect.DetectorFactory.seed = 0


# Common Control Characters considered whitespace
CC_WHITESPACE = (
    "\u0009",  # Horizontal Tab (TAB)
    "\u000A",  # Linefeed (LF)
    "\u000D",  # Carriage Return (CR)
)


# Unicode categories to remove during text normalization
UNICODE_FILTER = frozenset(
    {
        "Cc",
        "Cf",
        "Cn",
        "Co",
        "Cs",
        "Mc",
        "Me",
        "Mn",
        "Pc",
        "Pd",
        "Pe",
        "Pf",
        "Pi",
        "Ps",
    }
)


def extract_text(data):
    # type: (Readable) -> str
    """Extract plaintext from a text document file."""
    text = _extract_with_tika(data).get("content", "")
    return text or ""


def extract_text_metadata(data, **options):
    # type: (Readable, **Any) -> dict
    """Extract metadata from text document (title, language, characters).

    :param data: File with textual content
    :key text_guess_title: Guess title from content if not found in metadata.
    """
    opts = SdkOptions(**options)
    file = uread.open_data(data)
    tika_result = _extract_with_tika(file)

    result = {}

    # Aquire title
    title = _title_from_tika(tika_result, **opts.dict())
    if title:
        result["title"] = title

    txt_raw = tika_result.get("content") or ""
    txt_norm = normalize_text(txt_raw)

    # Number of characters
    result["characters"] = len(txt_norm)

    if not txt_norm:
        return result

    try:
        lang = langdetect.detect(txt_norm)
        logger.debug(f"Detected langauge: {lang}")
        result["language"] = langcodes.standardize_tag(lang)
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")

    return result


def extract_text_features(text, **options):
    # type: (str, **Any) -> dict
    """
    Create granular fingerprint for text (minhashes over ngrams from cdc-chunks).
    Text should be normalized before extracting text features.

    :param str text: Normalized plaintext.
    :key text_avg_chunk_size: Avg. number of chars per text chunk to be hashed.
    :key text_ngram_size: Sliding window size in number of characters.
    :returns dict: Dictionary with 'sizes' and 'features'.
    """
    opts = SdkOptions(**options)
    text = text.lower()
    chunks = chunk_text(text, text_avg_chunk_size=opts.text_avg_chunk_size)
    sizes = []
    feats = []
    for chunk in chunks:
        ngrams = (
            "".join(chars) for chars in sliding_window(chunk, opts.text_ngram_size)
        )
        features = [xxhash.xxh32_intdigest(s.encode("utf-8")) for s in ngrams]
        minimum_hash_digest = minhash_64(features)
        sizes.append(len(chunk))
        feats.append(encode_base64(minimum_hash_digest))
    return dict(kind=FeatureType.text.value, version=0, features=feats, sizes=sizes)


def normalize_text(text):
    # type: (Union[str, bytes], bool) -> str
    """Unicode normalization and character filtering."""

    # 1. Convert bytes to str
    if isinstance(text, bytes):
        text = text.decode("utf-8")

    # 2. Remove leading/trailing whitespace
    text_stripped = text.strip()

    # 3. Decompose with NFD
    text_decomposed = unicodedata.normalize("NFD", text_stripped)

    # 4. Filter
    chars = []
    for c in text_decomposed:
        cat = unicodedata.category(c)
        if cat not in UNICODE_FILTER:
            chars.append(c)
        elif c in CC_WHITESPACE:
            chars.append(c)
    text_filtered = "".join(chars)

    # 5. Collapse consecutive whitespace
    wsproc_text = " ".join(text_filtered.split())

    # 6. Recombine
    recombined = unicodedata.normalize("NFKC", wsproc_text)

    return recombined


def hash_text(text, **options):
    # type: (str, **Any) -> bytes
    """
    Create a 256-bit similarity preserving hash for text input.
    Text should be normalized before hash creation.
    """
    opts = SdkOptions(**options)
    text = text.lower()
    ngrams = ("".join(chars) for chars in sliding_window(text, opts.text_ngram_size))
    features = [xxhash.xxh32_intdigest(s.encode("utf-8")) for s in ngrams]
    shash = minhash_256(features)
    return shash


def chunk_text(text, **options):
    # type: (str, **Any) -> Generator[str]
    """
    Generates variable sized text chunks (without leading BOM)

    :param text: normalized plaintext
    :key: text_avg_chunk_size: Targeted average size of text chunks in bytes.
    """
    opts = SdkOptions(**options)
    avg_size = opts.text_avg_chunk_size
    data = text.encode("utf-32-be")
    avg_size *= 4  # 4 bytes per character
    for chunk in data_chunks(data, utf32=True, avg_chunk_size=avg_size):
        yield chunk.decode("utf-32-be")


def trim_text(text, nbytes):
    # type: (str, int) -> str
    """Trim text such that its utf-8 encoded size does not exceed nbytes."""
    return text.encode("utf-8")[:nbytes].decode("utf-8", "ignore").strip()


@lru_cache(typed=True)
def _extract_with_tika(data):
    # type: (Readable) -> dict
    """Extract text and metadata from a 'text'-file via Tika.
    Result:
        {"content": "...", "metadata": "..."}
    """
    file = uread.open_data(data)
    buffer = file.read()
    return tika_parser.from_buffer(buffer)


def _title_from_tika(tika_result, **options):
    # type: (dict, **Any) -> str
    """Extract title from tika result.

    Extraction is atempted in the following order
        - try to find title in tika metadata
        - use first line from text content

    :param tika_result: result from tika parsing
    :key: text_guess_title: whether to guess the title from the text itself as fallback.
    :key: meta_trim_title: Max number of bytes for utf-8 encoded title.
    """
    opts = SdkOptions(**options)
    title = ""
    meta = tika_result.get("metadata")
    mime_type = mime_clean(meta.get("Content-Type"))
    gmt = mime_to_gmt(mime_type)

    if meta:
        title = meta.get("dc:title", "")
        title = title[0].strip() if isinstance(title, list) else title.strip()
        if not title:
            title = meta.get("title", "")
            title = title[0].strip() if isinstance(title, list) else title.strip()

    # See if string would survive normalization
    norm_title = normalize_text(title)

    # Falback to get title from content
    if not norm_title and opts.text_guess_title and gmt == "text":
        content = tika_result.get("content", "")
        if content is not None:
            first_line = content.strip().splitlines()[0]
            title = trim_text(normalize_text(first_line), opts.meta_trim_title)

    return title


def name_from_uri(uri):
    """Extract "filename" part of an uri without file extension to be uses as fallback
    title for an asset if no title information can be aquired.
    """
    result = urlparse(uri)
    base = basename(result.path)
    name = splitext(base)[0]
    name = name.replace("-", " ")
    name = name.replace("_", " ")
    return name
