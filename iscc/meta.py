# -*- coding: utf-8 -*-
from os.path import basename, splitext
from urllib.parse import urlparse
from more_itertools import interleave, sliced
from iscc.text import normalize_text, trim_text
from iscc.schema import Opts
from iscc.utils import sliding_window
from iscc.simhash import similarity_hash
from blake3 import blake3
from iscc.mediatype import clean_mime, mime_to_gmt


WINDOW_SIZE_MID = 3


def meta_hash(title, extra=""):
    # type: (str, str) -> bytes
    """
    Calculate simmilarity preserving 256-bit hash digest from textual metadata.
    Text input should be normalized and trimmed before hashing. If the extra field
    is supplied we create separate hashes for title and extra and interleave them
    every 32-bit.
    """
    title = title.lower()
    title_n_grams = sliding_window(title, width=WINDOW_SIZE_MID)
    title_hash_digests = [blake3(s.encode("utf-8")).digest() for s in title_n_grams]
    simhash_digest = similarity_hash(title_hash_digests)

    # 4. Simhash extra metadata
    if extra:
        extra = extra.lower()
        extra_n_grams = sliding_window(extra, width=WINDOW_SIZE_MID)
        extra_hash_digests = [blake3(s.encode("utf-8")).digest() for s in extra_n_grams]
        extra_simhash_digest = similarity_hash(extra_hash_digests)

        simhash_digest = b"".join(
            interleave(sliced(simhash_digest, 4), sliced(extra_simhash_digest, 4))
        )

    return simhash_digest[:32]


def title_from_tika(tika_result: dict, guess=False, uri=None):
    """Extract title from tika result. Fallback to uri."""
    title = ""
    meta = tika_result.get("metadata")
    mime_type = clean_mime(meta.get("Content-Type"))
    gmt = mime_to_gmt(mime_type)

    if meta:
        title = meta.get("dc:title", "")
        title = title[0].strip() if isinstance(title, list) else title.strip()
        if not title:
            title = meta.get("title", "")
            title = title[0].strip() if isinstance(title, list) else title.strip()

    # See if string would survive normalization
    norm_title = normalize_text(title)

    if not norm_title and guess and gmt == "text":
        content = tika_result.get("content", "")
        if content is not None:
            first_line = content.strip().splitlines()[0]
            title = trim_text(normalize_text(first_line), Opts().meta_trim_title)

    if not title and uri is not None:
        result = urlparse(uri)
        base = basename(result.path)
        title = splitext(base)[0]
        title = title.replace("-", " ")
        title = title.replace("_", " ")
    return title
