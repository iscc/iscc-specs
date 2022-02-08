# -*- coding: utf-8 -*-
from pathlib import Path

from blake3 import blake3
from loguru import logger as log
import requests
from loguru import logger
import hashlib
import io
import os
import re
from typing import Sequence, Generator, Optional, Union
from urllib.parse import urlparse
from iscc import APP_DIR


def sliding_window(seq, width):
    # type: (Sequence, int) -> Generator[Sequence[Sequence]]
    """
    Generate a sequence of equal "width" slices each advancing by one elemnt.
    All types that have a length and can be sliced are supported (list, tuple, str ...).
    The result type matches the type of the input sequence.
    Fragment slices smaller than the width at the end of the sequence are not produced.
    If "witdh" is smaller than the input sequence than one element will be returned that
    is shorter than the requested width.
    """
    assert width >= 2, "Sliding window width must be 2 or bigger."
    idx = range(max(len(seq) - width + 1, 1))
    return (seq[i : i + width] for i in idx)


def download_file(url, folder=None, checksum=None, sanitize=False):
    # type: (str, Optional[Union[str, Path]], Optional[str], Optional[bool]) -> str
    """
    Download file to `folder` (default app_dir) and return file path.
    """
    url_obj = urlparse(url)
    file_name = os.path.basename(url_obj.path or url_obj.netloc)
    if sanitize:
        file_name = safe_filename(file_name)
    out_dir = folder or APP_DIR
    out_path = os.path.join(out_dir, file_name)
    if os.path.exists(out_path):
        logger.info(f"Already downloaded: {file_name}")
        if checksum:
            b3_calc = blake3(open(out_path, "rb").read()).hexdigest()
            assert checksum == b3_calc, f"Integrity error for {out_path}"
            return out_path

    log.info(f"downloading {url} to {out_path}")
    r = requests.get(url, stream=True)
    chunk_size = 1024 * 1024
    iter_size = 0
    with io.open(out_path, "wb") as fd:
        for chunk in r.iter_content(chunk_size):
            fd.write(chunk)
            iter_size += chunk_size

    if checksum:
        log.info(f"verifying {out_path}")
        b3_calc = blake3(open(out_path, "rb").read()).hexdigest()
        assert checksum == b3_calc, f"Integrity error for {out_path}"
    return out_path


def safe_filename(s: str, max_len: int = 255) -> str:
    """Sanitize a string making it safe to use as a filename.
    See: https://en.wikipedia.org/wiki/Filename.
    """
    ntfs_chars = [chr(i) for i in range(0, 31)]
    chars = [
        r'"',
        r"\#",
        r"\$",
        r"\%",
        r"'",
        r"\*",
        r"\,",
        r"\.",
        r"\/",
        r"\:",
        r'"',
        r"\;",
        r"\<",
        r"\>",
        r"\?",
        r"\\",
        r"\^",
        r"\|",
        r"\~",
        r"\\\\",
    ]
    pattern = "|".join(ntfs_chars + chars)
    regex = re.compile(pattern, re.UNICODE)
    fname = regex.sub("", s)
    return fname[:max_len].rsplit(" ", 0)[0]
