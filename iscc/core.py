# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
import base64
from io import BytesIO
from PIL.ImageOps import exif_transpose
from humanize import naturalsize
from loguru import logger
from typing import BinaryIO, List, Optional, Union, Any
from PIL import Image
import xxhash
from blake3 import blake3
from iscc.minhash import minhash_256
from iscc import text, image, audio, video

from iscc.codec import (
    Code,
    MT,
    ST,
    ST_CC,
    VS,
    encode_base32,
    write_header,
)
from iscc.cdc import data_chunks
from iscc.utils import Streamable
from iscc.mp7 import read_ffmpeg_signature
from iscc.meta import meta_hash
from iscc.schema import Opts
import langdetect
import langcodes

# Set for deterministic language detection
langdetect.DetectorFactory.seed = 0

###############################################################################
# High-Level ISCC Code generator functions                                   #
###############################################################################


def code_iscc():
    pass


def code_meta(title, extra="", **options):
    # type: (Union[str, bytes], Optional[Union[str, bytes]], **Any) -> dict
    """Generate Meta Code from title and extra metadata.

    :param str title: Used as input for first half of meta code
    :param str extra: Used as input for second half of meta code
    """
    opts = Opts(**options)
    nbits = opts.meta_bits
    nbytes = nbits // 8
    title_norm = text.normalize_text(title, lower=False)
    extra_norm = text.normalize_text(extra, lower=False)
    title_trimmed = text.trim_text(title_norm, opts.meta_trim_title)
    extra_trimmed = text.trim_text(extra_norm, opts.meta_trim_extra)
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


def code_content():
    pass


def code_text(txt, **options):
    # type: (Union[str, bytes], **Any) -> dict
    """Generate Content-ID Text"""
    opts = Opts(**options)

    nbits = opts.text_bits
    nbytes = nbits // 8
    txt = text.normalize_text(txt, lower=True)
    th = text.hash_text(txt)
    header = write_header(MT.CONTENT, ST_CC.TEXT, VS.V0, nbits)
    code = encode_base32(header + th[:nbytes])

    result = dict(code=code, characters=len(txt))

    try:
        result["language"] = langcodes.standardize_tag(langdetect.detect(txt))
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")

    if opts.text_granular:
        result["features"] = text.compute_text_features(txt, **options)

    return result


def code_image(img, **options):
    # type: (Union[str, BytesIO, Image.Image], **Any) -> dict

    opts = Opts(**options)
    nbits = opts.image_bits
    nbytes = nbits // 8
    assert nbits in (32, 64), "Content-ID Image does not yet support more than 64-bits"

    if not isinstance(img, Image.Image):
        # We cannot pass PIL Image for metadata extraction
        result = image.extract_image_metadata(img) or {}
        img = Image.open(img)
    else:
        logger.warning(f"Skipped image metadata extraction {img}")
        result = {}

    if opts.image_exif_transpose:
        img = exif_transpose(img)

    width, height = img.size
    result.update(dict(width=width, height=height))

    if opts.image_trim:
        img = image.trim_image(img)
        if img.size != result.values():
            tw, th = img.size
            result["trimmed"] = dict(width=tw, height=th)

    if opts.image_preview:
        preview = image.extract_image_preview(img, **options)
        preview_uri = image.encode_image_to_data_uri(preview, **options)
        result["preview"] = preview_uri

    pixels = image.normalize_image(img)
    hash_digest = image.hash_image(pixels)[:nbytes]
    header = write_header(MT.CONTENT, ST_CC.IMAGE, VS.V0, nbits)
    code = encode_base32(header + hash_digest)
    result["code"] = code

    return result


def code_audio(f, **options):
    # type: (Union[str, BinaryIO, List], **Any) -> dict
    """Generate Audio-ID from file(path) or Chromaprint features"""
    opts = Opts(**options)
    result = dict()
    nbits = opts.audio_bits
    nbytes = nbits // 8
    if isinstance(f, list):
        chroma = dict(fingerprint=f)
    else:
        chroma = audio.extract_audio_features(f, **options)
        result["duration"] = chroma["duration"]
        result.update(video.extract_video_metadata(f))

    shash_digest = audio.hash_audio(chroma["fingerprint"])

    if opts.audio_granular:
        features = audio.encode_audio_features(chroma["fingerprint"])
        result["features"] = features

    header = write_header(MT.CONTENT, ST_CC.AUDIO, VS.V0, nbits)
    code = encode_base32(header + shash_digest[:nbytes])
    result["code"] = code
    return result


def code_video(file, **options):
    # type: (File, **Any) -> dict
    """Compute Content-ID video.

    :param file: The video file.

    Returns a dictionary with the following fields:
        code: the calculated ISCC video code
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
    opts = Opts(**options)
    nbits = opts.video_bits

    result = video.extract_video_metadata(file)

    crop_value = video.detect_video_crop(file) if opts.video_crop else None
    signature = video.extract_video_signature(file, crop_value, **options)
    logger.debug(f"mp7 signature size {naturalsize(len(signature))}")
    frames = read_ffmpeg_signature(signature)
    logger.debug(f"mp7 signature frames {len(frames)}")
    features = [tuple(sig.vector.tolist()) for sig in frames]
    video_hash = video.hash_video(features, **options)
    video_code = Code((MT.CONTENT, ST_CC.VIDEO, VS.V0, nbits, video_hash))
    result["code"] = video_code.code
    result["signature_fps"] = opts.video_fps

    if crop_value:
        result["crop"] = crop_value.lstrip("crop=")

    if opts.video_include_mp7sig:
        result["mp7sig"] = base64.b64encode(signature).decode("ascii")

    if opts.video_preview:
        img_raw = video.extract_video_preview(file)
        result["preview"] = image.encode_image_to_data_uri(img_raw)

    if opts.video_granular is False:
        return result

    if opts.video_scenes:
        cutpoints = video.detect_video_scenes(file)
        features, durations = video.compute_video_features_scenes(frames, cutpoints)
        result["features"] = features
        result["sizes"] = durations
    else:
        features = video.compute_video_features_rolling(frames, **options)
        result["features"] = features
        result["window"] = opts.video_window
        result["overlap"] = opts.video_overlap

    return result


def code_data(data, **options):
    # type: (Union[str, BinaryIO, bytes, bytearray], **Any) -> dict
    opts = Opts(**options)
    nbits = opts.data_bits
    nbytes = nbits // 8

    # 1. & 2. XxHash32 over CDC-Chunks
    features = [xxhash.xxh32_intdigest(chunk) for chunk in data_chunks(data)]

    # 3. Apply minimum_hash
    data_hash = minhash_256(features)

    # 4. Encode with prepended component header
    header = write_header(MT.DATA, ST.NONE, VS.V0, nbits)
    code = encode_base32(header + data_hash[:nbytes])
    return dict(code=code)


def code_instance(data, **options):
    # type: (Union[str, BinaryIO, bytes], **Any) -> dict
    opts = Opts(**options)
    nbits = opts.instance_bits
    nbytes = nbits // 8
    filesize = 0
    b3 = blake3()
    with Streamable(data) as stream:
        while True:
            d = stream.stream.read(opts.io_chunk_size)
            if not d:
                break
            b3.update(d)
            filesize += len(d)

    datahash_digest = b3.digest()
    header = write_header(MT.INSTANCE, ST.NONE, VS.V0, nbits)
    code = encode_base32(header + datahash_digest[:nbytes])
    datahash = datahash_digest.hex()

    return dict(code=code, datahash=datahash, filesize=filesize)
