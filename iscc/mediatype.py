# -*- coding: utf-8 -*-
from loguru import logger
from typing import List, Optional, Union
import mimetypes
import magic
from PIL import Image
from iscc.schema import GMT, Readable
from iscc import uread


__all__ = [
    "mime_guess",
    "mime_normalize",
    "mime_supported",
    "mime_clean",
    "mime_to_gmt",
    "mime_from_name",
    "mime_from_data",
]


def mime_guess(data, file_name=None):
    # type: (Readable, str) -> str
    """Heuristic guessing of mediatype for different kinds of inputs.

    We try matching by file extension. If that fails we match by content sniffing.
    """

    guess_name, guess_data = None, None
    file = uread.open_data(data)

    if file_name is None:
        if hasattr(file, "name"):
            file_name = file.name
        elif hasattr(file, "filename"):
            file_name = file.filename

    if file_name:
        guess_name = mime_from_name(file_name)

    guess_data = mime_from_data(file.read(4096))

    # Normalize
    guess_data = mime_normalize(guess_data)
    guess_name = mime_normalize(guess_name)

    return guess_name or guess_data


def mime_normalize(mime: str) -> str:
    """Return normalized version of a mediatype."""
    return MEDIATYPE_NORM.get(mime, mime)


def mime_supported(mime: str) -> bool:
    """Check if mediatype is supported"""
    return mime_normalize(mime) in SUPPORTED_MEDIATYPES


def mime_from_name(name: str) -> Optional[str]:
    """Guess mediatype from filename or url."""
    return mimetypes.guess_type(name)[0]


def mime_from_data(data: bytes) -> Optional[str]:
    """Guess mediatype by sniffing raw header data."""
    return magic.from_buffer(data, mime=True)


def mime_clean(mime: Union[str, List]):
    """
    Clean mimetype/content-type string or first entry of a list of mimetype strings.
    Also removes semicolon separated encoding information.
    """
    if mime and isinstance(mime, List):
        mime = mime[0]
    if mime:
        mime = mime.split(";")[0]
    return mime.strip()


def mime_to_gmt(mime_type: str, file_path=None):
    """Get generic mediatype from mimetype."""
    mime_type = mime_clean(mime_type)
    if mime_type == "image/gif" and file_path:
        img = Image.open(file_path)
        if img.is_animated:
            return "video"
        else:
            return "image"
    entry = SUPPORTED_MEDIATYPES.get(mime_type)
    if entry:
        return entry["gmt"]
    gmt = mime_type.split("/")[0]
    if gmt in list(GMT):
        logger.warning(f"Guessing GMT from {mime_type}")
        return gmt


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
    # Note: pptx only detected by file extension. Sniffing gives 'application/zip'
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": {
        "gmt": "text",
        "ext": "pptx",
    },
    "application/vnd.ms-excel": {"gmt": "text", "ext": "xls"},
    # TODO add mobi support
    # "application/x-mobipocket-ebook": {
    #     "gmt": "text",
    #     "ext": ["mobi", "prc", "azw", "azw3", "azw4"],
    # },
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
    "audio/x-aiff": {"gmt": "audio", "ext": "aif"},
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

MEDIATYPE_NORM = {
    "audio/x-aiff": "audio/aiff",
    "image/x-ms-bmp": "image/bmp",
    "video/x-msvideo": "video/avi",
}

SUPPORTED_EXTENSIONS = []
for v in SUPPORTED_MEDIATYPES.values():
    ext = v["ext"]
    if isinstance(ext, str):
        SUPPORTED_EXTENSIONS.append(ext)
    else:
        for e in ext:
            SUPPORTED_EXTENSIONS.append(e)
