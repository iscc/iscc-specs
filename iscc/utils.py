# -*- coding: utf-8 -*-
import io
import os
from typing import BinaryIO, Union


File = Union[str, bytes, BinaryIO]


class Streamable:
    """Converts a file path or raw bytes into a managed readable stream."""

    def __init__(self, data: File):
        self.manage = True
        if isinstance(data, str):
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
