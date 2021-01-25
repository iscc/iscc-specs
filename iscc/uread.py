# -*- coding: utf-8 -*-
import io
import os
from os.path import basename, exists
from pathlib import Path
import mmap
from typing import Union, BinaryIO, Optional
from iscc.detect import detect


Readable = Union[str, Path, bytes, bytearray, memoryview, BinaryIO]


class uread:
    """
    Universal Reader.

    Can handle differnt inputs such as file paths or file-like objects.
    When used as a context manager it will only close the file if it was opened by
    uread else it will restore the file cursor after exit.
    """
    def __init__(self, uri, filename=None):
        # type: (Readable, Optional[str]) -> None
        self._uri = uri
        self._filename = filename
        self._size = None
        self._file = None
        self._data = None
        self._mediatype = None
        self._puid = None
        self._start_pos = None
        self._do_close = False

        if hasattr(uri, 'tell'):
            # Store eventual cursor to restore at exit.
            self._start_pos = uri.tell()

        if isinstance(uri, (str, Path)):
            if exists(uri):
                self._filename = self._filename or basename(uri)
                file = open(uri, mode="rb")
                self._do_close = True  # We manage lifecyle
                self._file = mmap.mmap(file.fileno(), length=0, access=mmap.ACCESS_READ)
        elif isinstance(uri, (bytes, bytearray, memoryview)):
            self._data = memoryview(uri)
            self._size = len(uri)
            self._file = io.BytesIO(self._data)
            self._filename = self._filename or "undefined.und"
        elif hasattr(uri, "read"):
            self._file = uri
        else:
            raise ValueError(f"Cannot open {uri}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._start_pos is not None:
            self.seek(self._start_pos)
        if self._do_close:
            self.close()

    def tell(self):
        return self._file.tell()

    def seek(self, pos, whence=0):
        return self._file.seek(pos, whence)

    def read(self, num):
        return self._file.read(num)

    def size(self):
        if self._size:
            return self._size
        elif hasattr(self._file, "size"):
            return self._file.size()
        elif hasattr(self._file, "fileno"):
            return os.fstat(self._file.fileno()).st_size

    @property
    def filename(self):
        if self._filename:
            return self._filename
        elif hasattr(self._file, "name"):
            return basename(self._file.name)
        elif hasattr(self._file, "filename"):
            return basename(self._file.filename)

    @property
    def mediatype(self):
        return self._mediatype or self._sniff().get("mediatype")

    @property
    def puid(self):
        return self._puid or self._sniff().get("puid")

    def _sniff(self):
        pos = self.tell()
        self.seek(0)
        data = self.read(4096)
        result = detect(data)
        self.seek(pos)
        self._mediatype = result.get("mediatype")
        self._puid = result.get("puid")
        return result

    def close(self):
        return self._file.close()
