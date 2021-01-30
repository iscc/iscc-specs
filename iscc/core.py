# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
from io import BytesIO

from PIL.ImageOps import exif_transpose
from loguru import logger
from typing import BinaryIO, List, Optional, Union
from PIL import Image
import xxhash
from blake3 import blake3
from iscc.minhash import minhash_256
from iscc.audio import audio_hash, encode_chomaprint, extract_chromaprint
from iscc.image import (
    image_data_uri,
    image_hash,
    image_metadata,
    image_normalize,
    image_thumbnail,
    image_trim,
)
from iscc.text import text_features, text_hash, text_normalize, text_trim
from iscc.codec import (
    Code,
    MT,
    ST,
    ST_CC,
    VS,
    decode_base32,
    encode_base32,
    write_header,
)
from iscc.params import *
from iscc.cdc import data_chunks
from iscc.utils import Streamable
from iscc.mp7 import read_ffmpeg_signature
from iscc.video import (
    compute_rolling_signatures,
    compute_scene_signatures,
    compute_video_hash,
    detect_crop,
    detect_scenes,
    extract_signature,
    video_metadata,
)
from iscc.simhash import similarity_hash
from iscc.meta import meta_hash
from iscc.schema import Opts
import langdetect
import langcodes

# Set for deterministic language detection
langdetect.DetectorFactory.seed = 0

###############################################################################
# Top-Level functions for generating ISCCs                                    #
###############################################################################


def meta_id(title, extra="", **kwargs):
    # type: (Union[str, bytes], Optional[Union[str, bytes]], **int) -> dict
    """Generate Meta Code from title and extra metadata.

    :param str title: Used as input for first half of meta code
    :param str extra: Used as input for second half of meta code
    """
    opts = Opts(**kwargs)
    nbits = opts.meta_bits
    nbytes = nbits // 8
    title_norm = text_normalize(title, lower=False)
    extra_norm = text_normalize(extra, lower=False)
    title_trimmed = text_trim(title_norm, opts.meta_trim_title)
    extra_trimmed = text_trim(extra_norm, opts.meta_trim_extra)
    mhash = meta_hash(title_trimmed, extra_trimmed)
    header = write_header(MT.META, ST.NONE, VS.V0, nbits)
    digest = header + mhash[:nbytes]
    code = encode_base32(digest)
    result = dict(
        code=code,
        title=title_trimmed,
    )
    if extra_trimmed:
        result["extra"] = extra_trimmed
    return result


def content_id_text(text, **kwargs):
    # type: (Union[str, bytes], **int) -> dict
    """Generate Content-ID Text"""
    opts = Opts(**kwargs)

    nbits = opts.text_bits
    nbytes = nbits // 8
    text = text_normalize(text, lower=True)
    th = text_hash(text)
    header = write_header(MT.CONTENT, ST_CC.TEXT, VS.V0, nbits)
    code = encode_base32(header + th[:nbytes])

    result = dict(code=code, characters=len(text))

    try:
        result["language"] = langcodes.standardize_tag(langdetect.detect(text))
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")

    if opts.text_granular:
        result["features"] = text_features(text, **kwargs)

    return result


def content_id_image(img, **kwargs):
    # type: (Union[str, BytesIO, Image.Image], **int) -> dict

    opts = Opts(**kwargs)
    nbits = opts.image_bits
    nbytes = nbits // 8
    assert nbits in (32, 64), "Content-ID Image does not yet support more than 64-bits"

    if not isinstance(img, Image.Image):
        # We cannot pass PIL Image for metadata extraction
        result = image_metadata(img) or {}
        img = Image.open(img)
    else:
        logger.warning(f"Skipped image metadata extraction {img}")
        result = {}

    if opts.image_exif_transpose:
        img = exif_transpose(img)

    width, height = img.size
    result.update(dict(width=width, height=height))

    if opts.image_trim:
        img = image_trim(img)
        if img.size != result.values():
            tw, th = img.size
            result["trimmed"] = dict(width=tw, height=th)

    if opts.image_preview:
        preview = image_thumbnail(img, **opts.dict())
        preview_uri = image_data_uri(preview, **opts.dict())
        result["preview"] = preview_uri

    pixels = image_normalize(img)
    hash_digest = image_hash(pixels)[:nbytes]
    header = write_header(MT.CONTENT, ST_CC.IMAGE, VS.V0, nbits)
    code = encode_base32(header + hash_digest)
    result["code"] = code

    return result


def content_id_audio(f, **kwargs):
    # type: (Union[str, BinaryIO, List], **int) -> dict
    """Generate Audio-ID from file(path) or Chromaprint features"""
    opts = Opts(**kwargs)
    result = dict()
    nbits = opts.audio_bits
    nbytes = nbits // 8
    if isinstance(f, list):
        chroma = dict(fingerprint=f)
    else:
        chroma = extract_chromaprint(f, **opts.dict())
        result["duration"] = chroma["duration"]
        result.update(video_metadata(f))

    shash_digest = audio_hash(chroma["fingerprint"])

    if opts.audio_granular:
        features = encode_chomaprint(chroma["fingerprint"])
        result["features"] = features

    header = write_header(MT.CONTENT, ST_CC.AUDIO, VS.V0, nbits)
    code = encode_base32(header + shash_digest[:nbytes])
    result["code"] = code
    return result


def content_id_video(video, scenes=False, crop=True, window=0, overlap=0, bits=64):
    # types: (File, bool, bool, int, int, int) -> dict
    """Compute Content-ID video.

    :param video: The video file.
    :param bool scenes: If True generate scene detection based granular features.
    :param bool crop: If True detect and remove black borders before processing.
    :param int window: Duration in seconds for rolling window based granular features.
    :param int overlap: Overlap in seconds for rolling window bases granular features.

    Returns a dictionary with the following fields:
        video_code: the calculated ISCC video code
        signature: raw bytes of extracted mp7 signature

    Optinally depending on settings these additional fields are provided:
        crop: the crop value that has been applied (if any) before signature extraction.
        features: list of base64 encoded granular video features.
        sizes: list of scene durations corresponding to features (only if scenes=True).
        window: window size of segements in seconds (only provided if scenes is False).
        overlap: overlap of segments in seconds (only provided if scenes is False).

    The window and overlap parameters are ignored if 0 or if scenes is False.
    Set crop=False if you know your video has no black borders to improve performance.
    """
    crop_value = detect_crop(video) if crop else None
    signature = extract_signature(video, crop_value)
    frames = read_ffmpeg_signature(signature)
    features = [tuple(sig.vector.tolist()) for sig in frames]
    video_hash = compute_video_hash(features, bits=bits)
    video_code = Code((MT.CONTENT, ST_CC.VIDEO, VS.V0, bits, video_hash))
    result = dict(
        code_video=video_code.code,
        # signature=signature,
    )
    if crop_value:
        result["crop"] = crop_value.lstrip("crop=")

    if scenes:
        cutpoints = detect_scenes(video)
        features, durations = compute_scene_signatures(frames, cutpoints)
        result["features"] = features
        result["sizes"] = durations
    elif any((window, overlap)):
        features = compute_rolling_signatures(frames, window=window, overlap=overlap)
        result["features"] = features
        result["window"] = window
        result["overlap"] = overlap

    return result


def content_id_mixed(cids, bits=64):
    # type: (List[str], int) -> str

    decoded = (decode_base32(code) for code in cids)
    truncated = [data[: bits // 8] for data in decoded]

    # 3. Apply Similarity hash
    simhash_digest = similarity_hash(truncated)
    header = write_header(MT.CONTENT, ST_CC.MIXED, VS.V0, bits)
    code = encode_base32(header + simhash_digest)
    return code


def data_id(data, bits=64):

    # 1. & 2. XxHash32 over CDC-Chunks
    features = [xxhash.xxh32_intdigest(chunk) for chunk in data_chunks(data)]

    # 3. Apply minimum_hash
    data_hash = minhash_256(features)

    # 4. Encode with prepended component header
    header = write_header(MT.DATA, ST.NONE, VS.V0, bits)
    code = encode_base32(header + data_hash[: bits // 8])
    return code


def instance_id(data, bits=64):
    # type: (Union[str, BinaryIO, bytes], int) -> List[str, str, int]

    size = 0
    b3 = blake3()
    with Streamable(data) as stream:
        while True:
            d = stream.stream.read(IID_READ_SIZE)
            if not d:
                break
            b3.update(d)
            size += len(d)

    top_hash_digest = b3.digest()
    header = write_header(MT.INSTANCE, ST.NONE, VS.V0, bits)
    n_bytes = bits // 8
    code = encode_base32(header + top_hash_digest[:n_bytes])
    tail = encode_base32(top_hash_digest[n_bytes:])

    return [code, tail, size]
