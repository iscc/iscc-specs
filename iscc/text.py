# -*- coding: utf-8 -*-
import unicodedata
from typing import Any, Generator, Union
import xxhash
from iscc.cdc import data_chunks
from iscc.minhash import compress, minhash, minhash_256
from iscc import uread
from iscc.schema import Opts
from iscc.utils import sliding_window
from iscc.codec import encode_base64
from iscc.schema import Readable
from tika import parser as tika_parser


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
    # type: (Union[Readable]) -> dict
    """Extract text and metadata from a 'text'-file via Tika.
    Result:
        {"content": "...", "metadata": "..."}
    """
    file = uread.open_data(data)
    buffer = file.read()
    return tika_parser.from_buffer(buffer)


def hash_text(text, **options):
    # type: (str, **Any) -> bytes
    """
    Create a 256-bit similarity preserving hash for text input.
    Text should be normalized before hash creation.
    """
    opts = Opts(**options)
    text = text.lower()
    ngrams = ("".join(chars) for chars in sliding_window(text, opts.text_ngram_size))
    features = [xxhash.xxh32_intdigest(s.encode("utf-8")) for s in ngrams]
    shash = minhash_256(features)
    return shash


def compute_text_features(text, **options):
    # type: (str, **Any) -> dict
    """
    Create granular fingerprint for text (minhashes over cdc-chunks).

    :param str text: Normalized plaintext.
    :param int text_avg_chunk_size: Average chunk size for detail hashes.
    :param int text_ngram_size: Sliding window size in number of characters.
    :returns dict: Dictionary with 'sizes' and 'features'
    """
    opts = Opts(**options)
    chunks = chunk_text(text, text_avg_chunk_size=opts.text_avg_chunk_size)
    sizes = []
    feats = []
    for chunk in chunks:
        ngrams = (
            "".join(chars) for chars in sliding_window(chunk, opts.text_ngram_size)
        )
        features = [xxhash.xxh32_intdigest(s.encode("utf-8")) for s in ngrams]
        minimum_hash = minhash(features)
        minimum_hash_digest = compress(minimum_hash, 1)
        sizes.append(len(chunk))
        feats.append(encode_base64(minimum_hash_digest))
    return dict(features=feats, sizes=sizes)


def chunk_text(text, **options):
    # type: (str, **Any) -> Generator[str]
    """
    Generates variable sized text chunks (without leading BOM)
    """
    opts = Opts(**options)
    avg_size = opts.text_avg_chunk_size
    data = text.encode("utf-32-be")
    avg_size *= 4  # 4 bytes per character
    for chunk in data_chunks(data, avg_size=avg_size, utf32=True):
        yield chunk.decode("utf-32-be")


def trim_text(text, nbytes):
    # type: (str, int) -> str
    """Trim text such that its utf-8 encoded size does not exceed nbytes."""
    return text.encode("utf-8")[:nbytes].decode("utf-8", "ignore").strip()


def normalize_text(text, lower=True):
    # type: (Union[str, bytes], bool) -> str
    """Unicode normalization and character filtering."""

    # 1. Convert bytes to str
    if isinstance(text, bytes):
        text = text.decode("utf-8")

    # 2. Remove leading/trailing whitespace
    text_stripped = text.strip()

    # 3. Lower case
    text_lower = text_stripped.lower() if lower else text_stripped

    # 4. Decompose with NFD
    text_decomposed = unicodedata.normalize("NFD", text_lower)

    # 5. Filter
    chars = []
    for c in text_decomposed:
        cat = unicodedata.category(c)
        if cat not in UNICODE_FILTER:
            chars.append(c)
        elif c in CC_WHITESPACE:
            chars.append(c)
    text_filtered = "".join(chars)

    # 6. Collapse consecutive whitespace
    wsproc_text = " ".join(text_filtered.split())

    # 7. Recombine
    recombined = unicodedata.normalize("NFKC", wsproc_text)

    return recombined
