# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
import json
from json import JSONDecodeError
from os.path import basename
import base64
import io
from PIL.ImageOps import exif_transpose
from humanize import naturalsize
from loguru import logger
from typing import List, Optional, Union, Any
from PIL import Image
import xxhash
from blake3 import blake3
from iscc.minhash import minhash_256
from pyld import jsonld
from iscc import jcs
from iscc import text, image, audio, video
from iscc.codec import (
    Code,
    MT,
    ST,
    ST_CC,
    VS,
    encode_base32,
    write_header,
    compose,
)
from iscc.cdc import data_chunks
from iscc.mp7 import read_ffmpeg_signature
from iscc.meta import meta_hash
from iscc.schema import (
    GMT,
    Options,
    Uri,
    Data,
    File,
    Readable,
)
from iscc.mediatype import mime_guess, mime_to_gmt
from iscc import uread
from iscc.data import extract_data_features, encode_data_features

from iscc.jldloader import requests_document_loader

jsonld.set_document_loader(requests_document_loader())

###############################################################################
# High-Level ISCC Code generator functions                                   #
###############################################################################


def code_iscc(uri, title=None, extra=None, **options):
    # type: (Union[Uri, File], Optional[str, dict], Optional[exec()], **Any) -> dict
    """Create a full ISCC.

    The full ISCC is a composite of Meta, Content, Data and Instance Codes.

    :param uri: File or filepath used for ISCC creation.
    :param title: Title of media asset (defaults to extracted metadata or filename)
    :param extra: Metadata to be used for Meta-Code generation
    :param options: See iscc.schema.Options for detailed ISCC generator options.
    """

    result = {"version": "0-0-0"}
    features = []

    file_obj = uread.open_data(uri)
    try:
        file_name = getattr(file_obj, "name", None)
        if file_name:
            result["filename"] = basename(file_name)

        instance = code_instance(file_obj, **options)
        result.update(instance)

        data = code_data(file_obj, **options)
        if "features" in data:
            features.append(data.pop("features"))
        result.update(data)

        content = code_content(file_obj, **options)
        if "features" in content:
            features.append(content.pop("features"))
        result.update(content)

        if features:
            result["features"] = features

        if not title:
            title = content.get("title")
        if not title and file_name:
            title = text.name_from_uri(file_name)

        meta = code_meta(title, extra, **options)
        result.update(meta)
        del result["code"]

        iscc_code_obj = compose(
            [meta["code"], content["code"], data["code"], instance["code"]]
        )
        result["iscc"] = iscc_code_obj.code
        concat = bytes.fromhex(result["metahash"]) + bytes.fromhex(result["datahash"])
        result["tophash"] = blake3(concat).hexdigest()
    finally:
        file_obj.close()

    return result


def code_meta(title, extra=None, **options):
    # type: (Union[str, bytes], Optional[Union[str, bytes, dict]], **Any) -> dict
    """Generate Meta Code from title and extra metadata.

    :param title: Used as input for first half of Meta-Code (or full if no extra)
    :param extra: Extended (str or dict) metadata used as input for second half of code.
    :key meta_bits: Length of generated Meta-Code in bits
    :key meta_ngram_size: Number of characters for sliding window over metadata text.
    :key meta_trim_title: Trim title length to this mumber of bytes
    :key meta_trim_extra: Trim extra data to this number of bytes
    :returns: Dict keys: code, title, matahash, (extra)
    """
    opts = Options(**options)
    nbits = opts.meta_bits
    nbytes = nbits // 8
    title_norm = text.normalize_text(title)

    if isinstance(extra, (str, bytes, bytearray)):
        try:
            extra = json.loads(extra)
        except JSONDecodeError:
            pass

    if extra is None:
        extra = ""
    elif isinstance(extra, dict):
        if "@context" in extra:
            extra = jsonld.normalize(
                extra, {"algorithm": "URDNA2015", "format": "application/n-quads"}
            )
        else:
            extra = jcs.canonicalize(extra)

    extra_norm = text.normalize_text(extra)
    title_trimmed = text.trim_text(title_norm, opts.meta_trim_title)
    extra_trimmed = text.trim_text(extra_norm, opts.meta_trim_extra)
    meta_simhash = meta_hash(title_trimmed, extra_trimmed, **options)
    header = write_header(MT.META, ST.NONE, VS.V0, nbits)
    digest = header + meta_simhash[:nbytes]
    code = encode_base32(digest)
    result = dict(
        code=code,
        title=title_trimmed,
    )
    if extra_trimmed:
        result["extra"] = extra_trimmed
    payload = title_trimmed + extra_trimmed
    result["metahash"] = blake3(payload.encode("utf-8")).hexdigest()
    return result


def code_content(data, **options):
    # type: (Union[Uri, File], **Any) -> dict
    """Detect mediatype and create corresponding Content-Code."""
    mediatype = mime_guess(data)
    gmt = mime_to_gmt(mediatype)

    if gmt == GMT.text:
        cc = code_text(data, **options)
    elif gmt == GMT.image:
        cc = code_image(data, **options)
    elif gmt == GMT.audio:
        cc = code_audio(data, **options)
    elif gmt == GMT.video:
        cc = code_video(data, **options)
    else:
        raise ValueError("Unknown mediatype")

    cc["mediatype"] = mediatype
    cc["gmt"] = gmt

    return cc


def code_text(data, **options):
    # type: (Readable, **Any) -> dict
    """Generate Content-ID Text

    :param data: Any kind of text document
    :key text_guess_title: whether to guess the title from the text itself as fallback.
    :key meta_trim_title: Max number of bytes for utf-8 encoded title.
    :key text_avg_chunk_size: Avg. number of chars per text chunk to be hashed.
    :key text_ngram_size: Sliding window size in number of characters.
    :key text_granular: Wether to extract granular text features
    """
    opts = Options(**options)
    nbits = opts.text_bits
    nbytes = nbits // 8
    result = {}

    f = uread.open_data(data)
    metadata = text.extract_text_metadata(f, **options)
    result.update(metadata)
    text_raw = text.extract_text(f)
    text_norm = text.normalize_text(text_raw)
    text_hash = text.hash_text(text_norm, **options)

    header = write_header(MT.CONTENT, ST_CC.TEXT, VS.V0, nbits)
    code = encode_base32(header + text_hash[:nbytes])
    result["code"] = code

    if opts.text_granular or opts.all_granular:
        features = text.extract_text_features(text_norm, **options)
        result["features"] = features

    return result


def code_image(data, **options):
    # type: (Union[Uri, Data, Image.Image], **Any) -> dict

    opts = Options(**options)
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

    if opts.image_preview or opts.all_preview:
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
    opts = Options(**options)
    result = dict()
    nbits = opts.audio_bits
    nbytes = nbits // 8
    if isinstance(data, list):
        chroma = dict(fingerprint=data)
    else:
        chroma = audio.extract_audio_features(data, **options)
        result.update(video.extract_video_metadata(data))

    shash_digest = audio.hash_audio(chroma["fingerprint"])

    if opts.audio_granular or opts.all_granular:
        features = audio.encode_audio_features(chroma["fingerprint"])
        result["features"] = features

    header = write_header(MT.CONTENT, ST_CC.AUDIO, VS.V0, nbits)
    code = encode_base32(header + shash_digest[:nbytes])
    result["code"] = code
    return result


def code_video(uri, **options):
    # type: (Union[Uri, File], **Any) -> dict
    """Compute Content-ID video."""
    opts = Options(**options)
    nbits = opts.video_bits

    result = {}
    metadata = video.extract_video_metadata(uri)
    result.update(metadata)

    crop_value = video.detect_video_crop(uri) if opts.video_crop else None
    signature = video.extract_video_signature(uri, crop_value, **options)
    logger.debug(f"mp7 signature size {naturalsize(len(signature))}")
    frames = read_ffmpeg_signature(signature)
    logger.debug(f"mp7 signature frames {len(frames)}")
    features = [tuple(sig.vector.tolist()) for sig in frames]
    video_hash = video.hash_video(features, **options)
    video_code = Code((MT.CONTENT, ST_CC.VIDEO, VS.V0, nbits, video_hash))
    result["code"] = video_code.code

    # Not yet part of schema
    # result["signature_fps"] = opts.video_fps
    # if crop_value:
    #     result["crop"] = crop_value.lstrip("crop=")

    if opts.video_include_fingerprint:
        result["fingerprint"] = base64.b64encode(signature).decode("ascii")

    if opts.video_preview or opts.all_preview:
        img_raw = video.extract_video_preview(uri)
        result["preview"] = image.encode_image_to_data_uri(img_raw)

    if opts.video_granular is False and opts.all_granular is False:
        return result

    if opts.video_scenes:
        cutpoints = video.detect_video_scenes(uri, **options)
        features = video.compute_video_features_scenes(frames, cutpoints)
    else:
        features = video.compute_video_features_rolling(frames, **options)

    result["features"] = features

    return result


def code_data(data, **options):
    # type: (Readable, **Any) -> dict
    """Create ISCC Data-Code.

    The Data-Code is a similarity preserving hash of the input data.

    :param data: File, filepath or raw data used for Data-Code creation.
    :key data_avg_chunk_size: Target chunk size in bytes for data chunking.
    :key data_granular: Return granular features (one hash per chunk).
    :key data_granular_factor: Size of granular data chunks times average chunk size.
    :key io_chunk_size: Number of bytes to read per IO operation.
    :return:
    """

    opts = Options(**options)
    nbits = opts.data_bits
    nbytes = nbits // 8
    features = []
    sizes = []

    for chunk in data_chunks(data, **options):
        sizes.append(len(chunk))
        features.append(xxhash.xxh32_intdigest(chunk))

    data_hash = minhash_256(features)
    header = write_header(MT.DATA, ST.NONE, VS.V0, nbits)
    code = encode_base32(header + data_hash[:nbytes])
    result = dict(code=code)

    if opts.data_granular or opts.all_granular:
        sizes, features = extract_data_features(data, **options)
        features = encode_data_features(sizes, features)
        result["features"] = features

    return result


def code_instance(data, **options):
    # type: (Readable, **Any) -> dict
    """Create ISCC Instance-Code.

    The Instance-Code is prefix of a cryptographic hash (blake3) of the input data.

    :param data: File, filepath or raw data used for Instance-Code creation.
    :key instance_bits: Length of generated Instance-Code in bits (default 64).
    :key io_chunk_size: Number of bytes to read per IO operation.
    :return: An InstanceCode object with attributes: code, datahash, filesize
    """
    opts = Options(**options)
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

    return dict(code=code, datahash=datahash, filesize=filesize)
