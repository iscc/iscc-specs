# -*- coding: utf-8 -*-"
"""High Level ISCC Generator"""
from tika import parser, detector
from iscc.mediatype import SUPPORTED_MEDIATYPES, mime_to_gmt
from iscc.meta import title_from_tika
from iscc.core import content_id_image, content_id_text, meta_id, content_id_video
from iscc.video import get_video_metadata


def compute(filepath, title="", extra=""):
    result = {}
    mediatype = detector.from_file(filepath)
    if mediatype not in SUPPORTED_MEDIATYPES:
        raise ValueError(f"Unsupported media type {mediatype}.")
    result["mediatype"] = mediatype
    tika_result = parser.from_file(filepath)

    if not title:
        title = title_from_tika(tika_result, guess=True, uri=filepath)

    meta_result = meta_id(title, extra)
    result.update(meta_result)

    gmt = mime_to_gmt(mediatype)
    result["gmt"] = gmt
    if gmt == "text":
        text = tika_result["content"]
        if not text:
            raise ValueError("Could not extract text")
        result["code_text"] = content_id_text(tika_result["content"])

    elif gmt == "image":
        result["code_image"] = content_id_image(filepath)
    elif gmt == "video":
        result.update(get_video_metadata(filepath))
        vid = content_id_video(filepath, scenes=True, crop=False)
        result.update(vid)
    result = {k: result[k] for k in sorted(result)}
    return result
