# -*- coding: utf-8 -*-
import io
import os
from pathlib import Path
from typing import BinaryIO, Sequence, Generator, Union


File = Union[str, bytes, BinaryIO, Path]


class Streamable:
    """Converts a file path or raw bytes into a managed readable stream."""

    def __init__(self, data: File):
        if isinstance(data, (str, Path)):
            self.stream = open(data, "rb")
            self.name = Path(data).name
        elif not hasattr(data, "read"):
            self.stream = io.BytesIO(data)
            self.name = ""
        else:
            self.stream = data
            self.name = ""

    def __enter__(self):
        return self

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
    All types that have a length and can be sliced are supported (list, tuple, str ...).
    The result type matches the type of the input sequence.
    Fragment slices smaller than the width at the end of the sequence are not produced.
    If "witdh" is smaller than the input sequence than one element will be returned that
    is shorter than the requested width.
    """
    assert width >= 2, "Sliding window width must be 2 or bigger."
    idx = range(max(len(seq) - width + 1, 1))
    return (seq[i : i + width] for i in idx)
