# -*- coding: utf-8 -*-
import unicodedata
from collections import Generator
from typing import List
import xxhash
from iscc.cdc import data_chunks
from iscc.minhash import compress, minhash, minhash_256
from iscc.utils import sliding_window
from codec import encode_base64

AVG_SIZE_TEXT = 1024  # Default average number of characters per text chunk
NGRAM_SIZE = 13  # Default number of characters per feature hash


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


def text_hash(text, window=NGRAM_SIZE):
    # type: (str, int) -> bytes
    """
    Create a 256-bit similarity preserving hash for text input.
    Text should be normalized before hash creation.
    """
    ngrams = ("".join(chars) for chars in sliding_window(text, window))
    features = [xxhash.xxh32_intdigest(s.encode("utf-8")) for s in ngrams]
    shash = minhash_256(features)
    return shash


def text_features(text, avg_size=AVG_SIZE_TEXT, ngram_size=NGRAM_SIZE):
    # type: (str, int, int) -> List[Tuple[int, str]]
    """
    Create granular fingerprint for text (minhashes over cdc-chunks).

    :param str text: Normalized plaintext.
    :param int avg_size: Average chunk size for detail hashes.
    :param int ngram_size: Sliding window size in number of characters.
    :returns list: Tuples of (chunksize, hash). Hash values are base64 encoded.
    """
    chunks = text_chunks(text, avg_size=avg_size)
    fingerprint = []
    for chunk in chunks:
        ngrams = ("".join(chars) for chars in sliding_window(chunk, ngram_size))
        features = [xxhash.xxh32_intdigest(s.encode("utf-8")) for s in ngrams]
        minimum_hash = minhash(features)
        minimum_hash_digest = compress(minimum_hash, 1)
        fingerprint.append((len(chunk), encode_base64(minimum_hash_digest)))
    return fingerprint


def text_chunks(text, avg_size=AVG_SIZE_TEXT):
    # type: (str, int) -> Generator[str]
    """
    Generates variable sized text chunks (without leading BOM)
    """
    data = text.encode("utf-32-be")
    avg_size *= 4  # 4 bytes per character
    for chunk in data_chunks(data, avg_size=avg_size, utf32=True):
        yield chunk.decode("utf-32-be")


def text_trim(text, nbytes):
    # type: (str, int) -> str
    """Trim text such that its utf-8 encoded size does not exceed nbytes."""
    return text.encode("utf-8")[:nbytes].decode("utf-8", "ignore").strip()


def text_normalize(text):
    # type: (Union[str, bytes]) -> str

    # 1. Convert bytes to str
    if isinstance(text, bytes):
        text = text.decode("utf-8")

    # 2. Remove leading/trailing whitespace
    text_stripped = text.strip()

    # 3. Lower case
    text_lower = text_stripped.lower()

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
