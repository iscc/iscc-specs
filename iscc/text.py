# -*- coding: utf-8 -*-
import json
import subprocess
import iscc_core.code_content_text
from iscc_core.code_content_text import Text
from loguru import logger as log
from os.path import basename, splitext
from typing import Any, Generator, Optional, Union
from urllib.parse import urlparse
import langdetect
import xxhash
from functools import lru_cache
import langcodes
import iscc.bin
from iscc.schema import FeatureType
from iscc_core.cdc import data_chunks
from iscc.options import SdkOptions, sdk_opts
from iscc import uread
from iscc.utils import sliding_window
from iscc_core.codec import encode_base64
from iscc.schema import Readable
from iscc_core.minhash import minhash_64, minhash_256


# Set for deterministic language detection
langdetect.DetectorFactory.seed = 0


def extract_text(data):
    # type: (Readable) -> str
    """Extract plaintext from a text document."""

    ufile = uread.open_data(data)
    cmd = [
        iscc.bin.java_bin(),
        "-jar",
        iscc.bin.tika_bin(),
        "--text",
        "--encoding=UTF-8",
    ]
    if hasattr(ufile, "name"):
        cmd.append(ufile.name)
        data = None
    else:
        data = ufile.read()
        if not data:
            log.warning(f"No data to extract text from {type(data)}")
            return ""

    try:
        result = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        iscc.bin.tika_install()
        result = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, check=True)

    return result.stdout.decode(encoding="UTF-8")


def extract_text_metadata(data, text=None, **options):
    # type: (Readable, Optional[str], **Any) -> dict
    """Extract metadata from text document (title, language, characters).

    :param Readable data: Readable with textual content
    :param str text: Extracted text
    :key bool text_guess_title: Guess title from content if not found in metadata.
    """
    opts = SdkOptions(**options) if options else sdk_opts
    ufile = uread.open_data(data)
    cmd = [
        iscc.bin.java_bin(),
        "-jar",
        iscc.bin.tika_bin(),
        "--metadata",
        "-j",
        "--encoding=UTF-8",
    ]

    if hasattr(ufile, "name"):
        cmd.append(ufile.name)
        data = None
    else:
        data = ufile.read()
        if not data:
            log.warning(f"No data to extract text metadata from {type(data)}")
            return {"characters": 0}

    try:
        result = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        iscc.bin.tika_install()
        result = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, check=True)

    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError:
        log.error("tike metadata json decode failed")
        metadata = {}

    title = metadata.get("dc:title", "")
    norm_title = normalize_text(title)

    # Falback to get title from content
    norm_text = normalize_text(text) if text else ""

    if not norm_title and opts.text_guess_title and text:
        title = text.strip().splitlines()[0]
        norm_title = normalize_text(title)

    norm_title = iscc_core.code_meta.trim_text(norm_title, opts.meta_trim_title)

    meta = {}
    if norm_title:
        meta["title"] = norm_title

    # Number of characters
    meta["characters"] = len(norm_text)

    try:
        lang = langdetect.detect(text)
        log.info(f"Detected langauge: {lang}")
        meta["language"] = langcodes.standardize_tag(lang)
    except Exception as e:
        log.warning(f"Language detection failed: {e}")

    return meta


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


@lru_cache(maxsize=4, typed=True)
def normalize_text(text):
    # type: (Text) -> str
    """
    Apply Unicode normalization and character filtering.

    Wraps iscc_core.normalize_text to support caching

    - Decode bytes to Unicode (assuming UTF-8 encoded text).
    - Remove leading/trailing whitespace.
    - Decompose with NFD normalization.
    - Filter special characters and whitespace.
    - Remove duplicate whitespace.
    - Recombine with NFKC normalization.

    :param Text text: Plain text to be normalized.
    :return: Normalized plain text.
    :rtype: str
    """
    return iscc_core.code_content_text.normalize_text(text)


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


def title_from_uri(uri):
    """Extract "filename" part of an uri without file extension to be uses as fallback
    title for an asset if no title information can be aquired.
    """
    result = urlparse(uri)
    base = basename(result.path)
    name = splitext(base)[0]
    name = name.replace("-", " ")
    name = name.replace("_", " ")
    return name
