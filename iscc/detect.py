# -*- coding: utf-8 -*-
"""File format identification"""
import os
from fido.fido import Fido, PerfTimer
from iscc.utils import File, Streamable


def detect(file):
    # type: (File) -> dict
    """Detect file type.

    Returns a dictionary with mediatype and puid. If detection fails it returns an
    empty dictionary.

    Example result: {"mediatype": "image/jpeg", "puid": "fmt/645"}

    see:
        https://www.iana.org/assignments/media-types/media-types.xhtml
        https://www.nationalarchives.gov.uk/PRONOM/
    """
    with Streamable(file, close=False) as stream:
        result = _detector.identify_stream(stream.stream, stream.name)

    if not result:
        return result

    # Override mediatype with eventual custom PUID mapping
    mtype = result.get("mediatype")
    result["mediatype"] = PRONOM_MEDIATYPE_MAP.get(result.get("puid"), mtype)

    # Normalize detected mediatype
    mtype = result.get("mediatype")
    result["mediatype"] = MIME_NORMALIZE_MAP.get(mtype, mtype)

    # Sort output map
    result = dict(sorted(result.items()))

    return result


class CustomFido(Fido):
    """Customized version of Fido (Format Idendification for Digital Objects).

    Customizations:
        - fix stream detection for python3
        - autodetect length and seekable
        - custom match handler
    """

    def blocking_read(self, file, bytes_to_read):
        """Override to fix endless blocking"""
        bytes_read = 0
        buffer = b""
        while bytes_read < bytes_to_read:
            readbuffer = file.read(bytes_to_read - bytes_read)
            buffer += readbuffer
            bytes_read = len(buffer)
            # CHANGED: to check against b'' instead of ''
            if readbuffer == b"":
                break
        return buffer

    def identify_stream(self, stream, filename, extension=True):
        """Override to detect length and seekability"""
        timer = PerfTimer()

        # CHANGED: Detect if object is seekable and if its length can be determined
        seekable = hasattr(stream, "seek")
        length = len(stream) if hasattr(stream, "__len__") else None
        bofbuffer, eofbuffer, bytes_read = self.get_buffers(
            stream, length=length, seekable=seekable
        )

        self.current_filesize = bytes_read
        self.current_file = "STDIN"
        matches = self.match_formats(bofbuffer, eofbuffer)
        # MdR: this needs attention
        if len(matches) > 0:
            # CHANGED: return instead of print
            return self.return_matches(
                self.current_file, matches, timer.duration(), "signature"
            )
        elif extension and (len(matches) == 0 or self.current_filesize == 0):
            # we can only determine the filename from the STDIN stream
            # on Linux, on Windows there is not a (simple) way to do that
            if os.name != "nt":
                try:
                    self.current_file = os.readlink("/proc/self/fd/0")
                except OSError:
                    if filename is not None:
                        self.current_file = filename
                    else:
                        self.current_file = "STDIN"
            else:
                if filename is not None:
                    self.current_file = filename
            matches = self.match_extensions(self.current_file)
            # we have to reset self.current_file if not on Windows
            if os.name != "nt":
                self.current_file = "STDIN"
            # CHANGED: return instead of print
            return self.return_matches(
                self.current_file, matches, timer.duration(), "extension"
            )

    def return_matches(self, fullname, matches, delta_t, matchtype=""):
        """Return matching data"""
        if len(matches) == 0:
            return {}
        f, sig_name = matches[0]
        mime = f.find("mime")
        result = dict(
            mediatype=mime.text if mime is not None else None, puid=self.get_puid(f)
        )
        return dict(sorted(result.items()))


_detector = CustomFido(
    quiet=True,
    zip=False,
    nocontainer=True,
    format_files=["formats-v96.xml", "format_extensions.xml"],
    containersignature_file="container-signature-20200121.xml",
)


# Custom mappings from PUID to mediatype
PRONOM_MEDIATYPE_MAP = {
    "fmt/414": "audio/x-aiff",
    "fido-fmt/189.word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "fmt/396": "application/x-mobipocket-ebook",
    "x-fmt/263": "application/xlsx",
    "fmt/649": "video/mpeg",
    "fmt/569": "video/x-matroska",
    "fmt/596": "video/mp4",
}

MIME_NORMALIZE_MAP = {
    "audio/aiff": "audio/x-aiff",
    "audio/vorbis": "audio/ogg",
    "video/theora": "video/ogg",
    "audio/wav": "audio/x-wav",
    "audio/wave": "audio/x-wav",
    "audio/vnd.wave": "audio/x-wav",
    "image/x-ms-bmp": "image/bmp",
    "application/vnd.adobe.photoshop": "image/vnd.adobe.photoshop",
    "image/psd": "image/vnd.adobe.photoshop",
    "application/CDFV2": "application/msword",
    "application/x-tika-msoffice": "application/msword",
    "text/rtf": "application/rtf",
    "application/xhtml+xml": "text/html",
    "text/xml": "application/xml",
    "video/avi": "video/x-msvideo",
    "application/mp4": "video/mp4",
    "application/x-matroska": "video/x-matroska",
}

SUPPORTED_MEDIATYPES = {
    # Text Formats
    "application/rtf": {"gmt": "text", "ext": "rtf"},
    "application/msword": {"gmt": "text", "ext": "doc"},
    "application/pdf": {"gmt": "text", "ext": "pdf"},
    "application/epub+zip": {"gmt": "text", "ext": "epub"},
    "application/xml": {"gmt": "text", "ext": "xml"},
    "application/xhtml+xml": {"gmt": "text", "ext": "xhtml"},
    "application/vnd.oasis.opendocument.text": {"gmt": "text", "ext": "odt"},
    "text/html": {"gmt": "text", "ext": "html"},
    "text/plain": {"gmt": "text", "ext": "txt"},
    "application/x-ibooks+zip": {"gmt": "text", "ext": "ibooks"},
    "text/x-web-markdown": {"gmt": "text", "ext": "md"},
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
    "audio/vnd.wave": {"gmt": "audio", "ext": "wav"},
    "audio/vorbis": {"gmt": "audio", "ext": "ogg"},
    "audio/x-aiff": {"gmt": "audio", "ext": "aif"},
    "audio/x-flac": {"gmt": "audio", "ext": "flac"},
    "audio/opus": {"gmt": "audio", "ext": "opus"},
    # Video Formats
    "application/vnd.rn-realmedia": {"gmt": "video", "ext": "rm"},
    "video/x-dirac": {"gmt": "video", "ext": "drc"},
    "video/3gpp": {"gmt": "video", "ext": "3gp"},
    "video/3gpp2": {"gmt": "video", "ext": "3g2"},
    "video/x-ms-asf": {"gmt": "video", "ext": "asf"},
    "video/x-msvideo": {"gmt": "video", "ext": "avi"},
    "video/webm": {"gmt": "video", "ext": "webm"},
    "video/mpeg": {"gmt": "video", "ext": ["mpeg", "mpg", "m1v", "vob"]},
    "video/mp4": {"gmt": "video", "ext": "mp4"},
    "video/x-m4v": {"gmt": "video", "ext": "m4v"},
    "video/x-matroska": {"gmt": "video", "ext": "mkv"},
    "video/theora": {"gmt": "video", "ext": ["ogg", "ogv"]},
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
