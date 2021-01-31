# -*- coding: utf-8 -*-"
"""High Level ISCC Generator"""
from tika import parser, detector
from iscc.mediatype import SUPPORTED_MEDIATYPES, mime_to_gmt
from iscc.meta import title_from_tika
from iscc.video import extract_video_metadata
import iscc


def compute(filepath, title="", extra=""):
    result = {}
    mediatype = detector.from_file(filepath)
    if mediatype not in SUPPORTED_MEDIATYPES:
        raise ValueError(f"Unsupported media type {mediatype}.")
    result["mediatype"] = mediatype
    tika_result = parser.from_file(filepath)

    if not title:
        title = title_from_tika(tika_result, guess=True, uri=filepath)

    meta_result = iscc.meta_id(title, extra)
    meta_result["code_meta"] = meta_result.pop("code")
    result.update(meta_result)

    gmt = mime_to_gmt(mediatype)
    result["gmt"] = gmt

    # Content Code
    if gmt == "text":
        text = tika_result["content"]
        if not text:
            raise ValueError("Could not extract text")
        result["code_text"] = iscc.content_id_text(tika_result["content"])
    elif gmt == "image":
        result["code_image"] = iscc.content_id_image(filepath)
    elif gmt == "video":
        result.update(extract_video_metadata(filepath))
        vid = iscc.content_id_video(
            filepath,
            video_granular=True,
            video_scenes=True,
            video_crop=False,
        )
        result.update(vid)

    # Data Code
    result["code_data"] = iscc.data_id(filepath)

    # Instance Code
    iid, tail, size = iscc.instance_id(filepath)
    result["code_instance"] = iid

    result = {k: result[k] for k in sorted(result)}
    return result


def create_meta_code(fp, meta=None):

    pass


def create_content_code():
    pass


def create_data_code():
    pass


def create_instance_code():
    pass
