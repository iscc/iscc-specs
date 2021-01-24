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
    def __init__(self, uri, filename=None):
        # type: (Readable, Optional[str]) -> None
        self._uri = uri
        self._filename = filename
        self._size = None
        self._file = None
        self._data = None
        self._mediatype = None
        self._puid = None

        if isinstance(uri, (str, Path)):
            if exists(uri):
                self._filename = self._filename or basename(uri)
                file = open(uri, mode="rb")
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

        self.seek(0)

    def tell(self):
        return self._file.tell()

    def seek(self, pos, whence=0):
        return self._file.seek(pos, whence)

    def read(self, num):
        return self._file.read(num)

    @property
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

    def view(self):
        if self._data:
            return io.BytesIO(self._data)
        elif hasattr(self._file, "fileno"):
            return open(self._file.name, "rb")
        else:
            return io.BytesIO(self._file)

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
