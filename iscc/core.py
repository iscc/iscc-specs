# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
import base64
import io
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
from iscc.mp7 import read_ffmpeg_signature
from iscc.meta import meta_hash, title_from_tika
from iscc.schema import GMT, Opts, Uri, Data, File, Readable
from iscc.mediatype import guess_mediatype, mime_to_gmt
import langdetect
import langcodes
from tika import parser as tika_parser
from iscc import uread


# Set for deterministic language detection
from schema import InstanceCode


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


def code_content(data, **options):
    # type: (Union[Uri, Data], **Any) -> dict
    """Detect mediatype and create corresponding Content-Code."""
    mediatype = guess_mediatype(data)
    gmt = mime_to_gmt(mediatype)
    if gmt == GMT.text:
        return code_text(data, **options)
    elif gmt == GMT.image:
        return code_image(data, **options)
    elif gmt == GMT.audio:
        return code_audio(data, **options)
    elif gmt == GMT.video:
        return code_video(data, **options)
    else:
        raise ValueError("Unknown mediatype")


def code_text(data, **options):
    # type: (Union[Data, Uri], **Any) -> dict
    """Generate Content-ID Text"""
    opts = Opts(**options)
    nbits = opts.text_bits
    nbytes = nbits // 8
    result = {}

    with uread.open_data(data) as f:
        tika_result = tika_parser.from_buffer(f.read())

    # Metadata
    title = title_from_tika(tika_result, guess=True)
    if title:
        result["title"] = title

    # Content-Code
    txt = tika_result["content"] or ""
    txt = text.normalize_text(txt, lower=True)
    th = text.hash_text(txt)
    header = write_header(MT.CONTENT, ST_CC.TEXT, VS.V0, nbits)
    code = encode_base32(header + th[:nbytes])

    result["code"] = code
    result["characters"] = len(txt)

    try:
        result["language"] = langcodes.standardize_tag(langdetect.detect(txt))
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")

    if opts.text_granular:
        result["features"] = text.compute_text_features(txt, **options)

    return result


def code_image(data, **options):
    # type: (Union[Uri, Data, Image.Image], **Any) -> dict

    opts = Opts(**options)
    nbits = opts.image_bits
    nbytes = nbits // 8
    assert nbits in (32, 64), "Content-ID Image does not yet support more than 64-bits"

    try:
        result = image.extract_image_metadata(data) or {}
    except Exception as e:
        logger.error(f"Failed image metadata extraction: {e}")
        result = {}

    if isinstance(data, Image.Image):
        img_obj = data
    else:
        with uread.open_data(data) as infile:
            img_obj = Image.open(io.BytesIO(infile.read()))

    if opts.image_exif_transpose:
        img_obj = exif_transpose(img_obj)

    width, height = img_obj.size
    result.update(dict(width=width, height=height))

    if opts.image_trim:
        img_obj = image.trim_image(img_obj)
        if img_obj.size != result.values():
            tw, th = img_obj.size
            result["trimmed"] = dict(width=tw, height=th)

    if opts.image_preview:
        preview = image.extract_image_preview(img_obj, **options)
        preview_uri = image.encode_image_to_data_uri(preview, **options)
        result["preview"] = preview_uri

    pixels = image.normalize_image(img_obj)
    hash_digest = image.hash_image(pixels)[:nbytes]
    header = write_header(MT.CONTENT, ST_CC.IMAGE, VS.V0, nbits)
    code = encode_base32(header + hash_digest)
    result["code"] = code

    return result


def code_audio(data, **options):
    # type: (Union[Uri, Data, List], **Any) -> dict
    """Generate Audio-ID from file(path) or Chromaprint features"""
    opts = Opts(**options)
    result = dict()
    nbits = opts.audio_bits
    nbytes = nbits // 8
    if isinstance(data, list):
        chroma = dict(fingerprint=data)
    else:
        chroma = audio.extract_audio_features(data, **options)
        result["duration"] = chroma["duration"]
        result.update(video.extract_video_metadata(data))

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
        cutpoints = video.detect_video_scenes(file, **options)
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
    # type: (Readable, **Any) -> InstanceCode
    """Create ISCC Instance-Code

    :param Readable data: File, filepath or raw data used for Instance-Code creation.
    :key instance_bits: Length of generated Instance-Code in bits (default 64).
    :key io_chunk_size: Number of bytes to read per IO operation.
    :return: A dictionary including keys: code, datahash, filesize
    """
    opts = Opts(**options)
    nbits = opts.instance_bits
    nbytes = nbits // 8
    filesize = 0
    b3 = blake3()
    stream = uread.open_data(data)

    buffer = stream.read(opts.io_chunk_size)
    while buffer:
        filesize += len(buffer)
        b3.update(buffer)
        buffer = stream.read(opts.io_chunk_size)

    datahash_digest = b3.digest()
    header = write_header(MT.INSTANCE, ST.NONE, VS.V0, nbits)
    code = encode_base32(header + datahash_digest[:nbytes])
    datahash = datahash_digest.hex()

    return InstanceCode(code=code, datahash=datahash, filesize=filesize)
