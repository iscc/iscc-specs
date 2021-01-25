# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional, Union
from os import path
import mimetypes
import magic
import io


def guess(data):
    # type: (Union[Path, str, bytes, bytearray, memoryview, io.BufferedReader]) -> str
    """Heuristic guessing of mediatype for different kinds of inputs.

    We try matching by file extension. If that fails we match by content sniffing.
    """

    guess_name, guess_data = None, None

    if isinstance(data, Path):
        data = data.as_posix()

    if isinstance(data, str):
        guess_name = from_name(data)
        if path.isfile(data):
            with open(data, "rb") as infile:
                guess_data = from_data(infile.read(4096))

    if isinstance(data, (bytes, bytearray)):
        guess_data = from_data(data)

    if isinstance(data, memoryview):
        guess_data = from_data(bytes(data))

    if isinstance(data, io.BufferedReader) and hasattr(data, "name"):
        guess_name = from_name(data.name)
        with open(data.name, "rb") as infile:
            guess_data = from_data(infile.read(4096))

    return guess_name or guess_data


def from_name(name: str) -> Optional[str]:
    """Guess mediatype from filename or url."""
    return mimetypes.guess_type(name)[0]


def from_data(data: bytes) -> Optional[str]:
    """Guess mediatype by sniffing raw header data."""
    return magic.from_buffer(data, mime=True)


mimetypes.add_type("text/markdown", ".md")
mimetypes.add_type("text/markdown", ".markdown")
mimetypes.add_type("application/x-mobipocket-ebook", ".mobi")
mimetypes.add_type("application/x-sqlite3", ".sqlite")


SUPPORTED_MEDIATYPES = {
    # Text Formats
    "application/rtf": {"gmt": "text", "ext": "rtf"},
    "application/msword": {"gmt": "text", "ext": "doc"},
    "application/pdf": {"gmt": "text", "ext": "pdf"},
    "application/epub+zip": {"gmt": "text", "ext": "epub"},
    "text/xml": {"gmt": "text", "ext": "xml"},
    "application/json": {"gmt": "text", "ext": "json"},
    "application/xhtml+xml": {"gmt": "text", "ext": "xhtml"},
    "application/vnd.oasis.opendocument.text": {"gmt": "text", "ext": "odt"},
    "text/html": {"gmt": "text", "ext": "html"},
    "text/plain": {"gmt": "text", "ext": "txt"},
    "application/x-ibooks+zip": {"gmt": "text", "ext": "ibooks"},
    "text/markdown": {"gmt": "text", "ext": ["md", "markdown"]},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
        "gmt": "text",
        "ext": "docx",
    },
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
        "gmt": "text",
        "ext": "xlsx",
    },
    "application/vnd.ms-excel": {"gmt": "text", "ext": "xls"},
    "application/x-mobipocket-ebook": {
        "gmt": "text",
        "ext": ["mobi", "prc", "azw", "azw3", "azw4"],
    },
    # Image Formats
    "image/bmp": {"gmt": "image", "ext": "bmp"},
    "image/gif": {"gmt": "image", "ext": "gif"},
    "image/jpeg": {"gmt": "image", "ext": ["jpg", "jpeg"]},
    "image/png": {"gmt": "image", "ext": "png"},
    "image/tiff": {"gmt": "image", "ext": "tif"},
    "image/vnd.adobe.photoshop": {"gmt": "image", "ext": "psd"},
    "application/postscript": {"gmt": "image", "ext": "eps"},
    # Audio Formats
    "audio/mpeg": {"gmt": "audio", "ext": "mp3"},
    "audio/wav": {"gmt": "audio", "ext": "wav"},
    "audio/ogg": {"gmt": "audio", "ext": "ogg"},
    "audio/aiff": {"gmt": "audio", "ext": "aif"},
    "audio/x-flac": {"gmt": "audio", "ext": "flac"},
    "audio/opus": {"gmt": "audio", "ext": "opus"},
    # Video Formats
    "application/vnd.rn-realmedia": {"gmt": "video", "ext": "rm"},
    "video/x-dirac": {"gmt": "video", "ext": "drc"},
    "video/3gpp": {"gmt": "video", "ext": "3gp"},
    "video/3gpp2": {"gmt": "video", "ext": "3g2"},
    "video/x-ms-asf": {"gmt": "video", "ext": "asf"},
    "video/avi": {"gmt": "video", "ext": "avi"},
    "video/webm": {"gmt": "video", "ext": "webm"},
    "video/mpeg": {"gmt": "video", "ext": ["mpeg", "mpg", "m1v", "vob"]},
    "video/mp4": {"gmt": "video", "ext": "mp4"},
    "video/x-m4v": {"gmt": "video", "ext": "m4v"},
    "video/x-matroska": {"gmt": "video", "ext": "mkv"},
    "video/ogg": {"gmt": "video", "ext": ["ogg", "ogv"]},
    "video/quicktime": {"gmt": "video", "ext": ["mov", "f4v"]},
    "video/x-flv": {"gmt": "video", "ext": "flv"},
    "application/x-shockwave-flash": {"gmt": "video", "ext": "swf"},
    "video/h264": {"gmt": "video", "ext": "h264"},
    "video/x-ms-wmv": {"gmt": "video", "ext": "wmv"},
}

SUPPORTED_EXTENSIONS = []
for v in SUPPORTED_MEDIATYPES.values():
    ext = v["ext"]
    if isinstance(ext, str):
        SUPPORTED_EXTENSIONS.append(ext)
    else:
        for e in ext:
            SUPPORTED_EXTENSIONS.append(e)


if __name__ == "__main__":
    import iscc_samples as samples

    for fp in samples.all():
        by_name = from_name(fp.as_posix())
        by_data = from_data(fp.open(mode="rb").read())
        by_guess = guess(fp.as_posix())
        print(fp.name, end=" ")
        print(by_name, end=" ")
        print(by_data, end=" ")
        print(by_guess, end=" ")
        if fp.name not in ("demo.sqlite", "demo.f4v"):
            assert by_guess in SUPPORTED_MEDIATYPES, fp.name
        print()
