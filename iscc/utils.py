# -*- coding: utf-8 -*-
import io
import os
from pathlib import Path
from typing import BinaryIO, Sequence, Generator, Union


File = Union[str, bytes, BinaryIO, Path]


class Streamable:
    """Converts a file path or raw bytes into a managed readable stream."""

    def __init__(self, data: File):
        self.manage = True
        if isinstance(data, (str, Path)):
            self.stream = open(data, "rb")
        elif not hasattr(data, "read"):
            self.stream = io.BytesIO(data)
        else:
            self.stream = data
            self.manage = False

    def __enter__(self):
        return self.stream

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stream.close()


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


def sliding_window(seq, width):
    # type: (Sequence, int) -> Generator[Sequence[Sequence]]
    """
    Generate a sequence of equal "width" slices each advancing by one elemnt.
    All types that have a length and can be sliced are supported (list, tuple, str ...)
    and retain there types the result sequence.
    Fragment slices smaller than the width at the end of the sequence are not produced.
    If "witdh" is smaller the the input sequence than one element will be returned that
    is shorter that the requested width.
    """
    assert width >= 2, "Sliding window width must be 2 or bigger."
    idx = range(max(len(seq) - width + 1, 1))
    return (seq[i : i + width] for i in idx)
