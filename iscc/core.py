# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
import gzip
import os.path
import iscc_core
from iscc_core.code_content_text import normalize_text
from os.path import basename
import base64
import io
import mobi
from codetiming import Timer
from humanize import naturalsize
from loguru import logger as log
from typing import List, Optional, Union, Any
from PIL import Image
from blake3 import blake3
import iscc
from iscc import jcs
from iscc import text, image, audio, video
from iscc.mp7 import read_ffmpeg_signature
from iscc.schema import (
    GMT,
    Options,
    Uri,
    Data,
    File,
    Readable,
    ISCC,
)
from iscc.mediatype import mime_guess, mime_to_gmt
from iscc import uread
from iscc.data import encode_data_features


###############################################################################
# High-Level ISCC Code generator functions                                   #
###############################################################################


def code_iscc(uri, title=None, extra=None, **options):
    # type: (Union[Uri, File], Union[str, bytes], Union[None, str, bytes, dict], **Any) -> dict
    """Create a full ISCC.

    The full ISCC is a composite of Meta, Content, Data and Instance Codes.

    :param uri: File or filepath used for ISCC creation.
    :param title: Title of media asset (defaults to extracted metadata or filename)
    :param extra: Metadata to be used for Meta-Code generation
    :param options: See iscc.schema.Options for detailed ISCC generator options.
    """
    opts = Options(**options)
    result = {"version": "0-0-0"}
    features = []

    file_obj = uread.open_data(uri)

    file_name = getattr(file_obj, "name", None)
    if file_name:
        result["filename"] = basename(file_name)

    with Timer(text="instance code creation took {:0.4f}s", logger=log.debug):
        instance = code_instance(file_obj, **options)
    result.update(instance)

    with Timer(text="data code creation took {:0.4f}s", logger=log.debug):
        data = code_data(file_obj, **options)

    if "features" in data:
        features.append(data.pop("features"))
    result.update(data)

    content = code_content(file_obj, **options)

    # TODO generalize to store extracts from all mediatypes (mp7, chroma,...)
    if opts.text_store and "plaintext" in content:
        plaintext = content.pop("plaintext")
        path = os.path.dirname(file_obj.name)
        outpath = os.path.join(path, instance["datahash"] + ".txt.gz")
        with gzip.open(outpath, "wb") as outf:
            outf.write(plaintext.encode("utf-8"))
        log.debug(f"Stored plaintext at: {outpath}")

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

    iscc_code_obj = iscc_core.compose(
        [meta["code"], content["code"], data["code"], instance["code"]]
    )
    result["iscc"] = iscc_code_obj.code
    concat = bytes.fromhex(result["metahash"]) + bytes.fromhex(result["datahash"])
    result["tophash"] = blake3(concat).hexdigest()
    valid = ISCC(**result)

    return valid.dict(exclude_unset=True)


def code_meta(title, extra=None, **options):
    # type: (Union[str, bytes], Union[None, str, bytes, dict], **Any) -> dict
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
    extra = None if extra in (b"", "", bytearray(), None) else extra

    if isinstance(extra, dict):
        extra = jcs.canonicalize(extra).decode("utf-8")
        log.debug("Metadata JSON encoded and conanicalized with JCS")

    meta_code = iscc_core.gen_meta_code_v0(
        title=title, extra=extra, bits=opts.meta_bits
    )
    return meta_code.dict(exclude_unset=True, exclude={"binary"}, exclude_none=True)


def code_content(data, **options):
    # type: (Union[Uri, File], **Any) -> dict
    """Detect mediatype and create corresponding Content-Code."""
    mediatype = mime_guess(data)
    gmt = mime_to_gmt(mediatype)

    is_mobi = mediatype == "application/x-mobipocket-ebook"
    if is_mobi:
        tempdir, data = mobi.extract(data)

    if gmt == GMT.text:
        with Timer(text="content code text creation took {:0.4f}s", logger=log.debug):
            cc = code_text(data, **options)
    elif gmt == GMT.image:
        with Timer(text="content code image creation took {:0.4f}s", logger=log.debug):
            cc = code_image(data, **options)
    elif gmt == GMT.audio:
        with Timer(text="content code audio creation took {:0.4f}s", logger=log.debug):
            cc = code_audio(data, **options)
    elif gmt == GMT.video:
        with Timer(text="content code video creation took {:0.4f}s", logger=log.debug):
            cc = code_video(data, **options)
    else:
        raise ValueError("Unsupported mediatype: {}".format(mediatype))

    cc["mediatype"] = mediatype
    cc["gmt"] = gmt

    return cc


def code_text(data, **options):
    # type: (Readable, **Any) -> dict
    """Generate Content-ID Text

    :param data: Any kind of text document
    """
    opts = Options(**options)
    result = {}

    f = uread.open_data(data)
    metadata = text.extract_text_metadata(f, **options)
    result.update(metadata)
    text_raw = text.extract_text(f)
    text_code = iscc_core.gen_text_code_v0(text_raw, bits=opts.text_bits)
    result.update(text_code.dict(exclude_unset=True))

    granular = (
        opts.all_granular if isinstance(opts.all_granular, bool) else opts.text_granular
    )
    if granular:
        text_norm = normalize_text(text_raw)
        features = text.extract_text_features(text_norm, **options)
        result["features"] = features

    if opts.text_store:
        result["plaintext"] = text_raw

    return result


def code_image(data, **options):
    # type: (Union[Readable], **Any) -> dict
    """Generate Content-Code Image

    :param data: raw data, file or path to image
    :key bool image_granular: Wether to compute granular image features
    :key int image_granular_n: Number of features to compute (default 32)
    """
    opts = Options(**options)

    try:
        result = image.extract_image_metadata(data) or {}
    except Exception as e:
        log.error(f"Failed image metadata extraction: {e}")
        result = {}

    stream = uread.open_data(data)
    image_code = iscc_core.gen_image_code_v0(stream, bits=opts.image_bits)
    result.update(image_code.dict(exclude_unset=True))

    if isinstance(data, Image.Image):
        img_obj = data
    else:
        img_obj = Image.open(io.BytesIO(uread.open_data(data).read()))

    # TODO review  image exif_transpose and trimming
    # if opts.image_exif_transpose:
    #     img_obj = exif_transpose(img_obj)
    #
    # if opts.image_trim:
    #     img_obj = image.trim_image(img_obj)
    #     # if img_obj.size != result.values():
    #     #     tw, th = img_obj.size
    #     #     result["trimmed"] = dict(width=tw, height=th)

    granular = (
        opts.all_granular
        if isinstance(opts.all_granular, bool)
        else opts.image_granular
    )
    if granular:
        try:
            feat_obj = image.extract_image_features(data, n=opts.image_granular_n)
            result["features"] = feat_obj
        except Exception as e:
            log.error("image feature extraction failed")
            log.exception(e)

    do_preview = (
        opts.all_preview if isinstance(opts.all_preview, bool) else opts.image_preview
    )

    if do_preview:
        preview = image.extract_image_preview(img_obj, **options)
        preview_uri = image.encode_image_to_data_uri(preview, **options)
        result["preview"] = preview_uri

    return result


def code_audio(data, **options):
    # type: (Union[Uri, Data, List], **Any) -> dict
    """Generate Audio-ID from file(path) or Chromaprint features"""
    opts = Options(**options)
    result = dict()

    if isinstance(data, list):
        chroma = dict(fingerprint=data)
    else:
        chroma = audio.extract_audio_features(data, **options)
        # TODO: implement custom audio metadata extraction
        metadata = video.extract_video_metadata(data)
        # We remove video related keys that are detected in some audio files.
        metadata.pop("fps", None)
        metadata.pop("width", None)
        metadata.pop("height", None)
        result.update(metadata)

    audio_code = iscc_core.gen_audio_code_v0(
        cv=chroma["fingerprint"], bits=opts.audio_bits
    )
    granular = (
        opts.all_granular
        if isinstance(opts.all_granular, bool)
        else opts.audio_granular
    )
    if granular:
        features = audio.encode_audio_features(chroma["fingerprint"])
        result["features"] = features

    result["code"] = audio_code.code
    return result


def code_video(uri, **options):
    # type: (Union[Uri, File], **Any) -> dict
    """Compute Content-ID video."""
    opts = Options(**options)
    result = {}
    metadata = video.extract_video_metadata(uri)
    result.update(metadata)

    crop_value = video.detect_video_crop(uri) if opts.video_crop else None

    granular = (
        opts.all_granular
        if isinstance(opts.all_granular, bool)
        else opts.video_granular
    )
    do_ffmpeg_scenes = granular and opts.video_scenes_ffmpeg

    if do_ffmpeg_scenes:
        signature, cutpoints = video.extract_video_signature_cutpoints(
            uri, crop_value, **options
        )
    else:
        signature = video.extract_video_signature(uri, crop_value, **options)

    with Timer(text="video signature decoding took {:0.4f}s", logger=log.debug):
        frames = read_ffmpeg_signature(signature)
    log.debug(f"video sig {naturalsize(len(signature))} with {len(frames)} frames")
    features = [tuple(sig.vector.tolist()) for sig in frames]
    video_code = iscc_core.gen_video_code_v0(features, bits=opts.video_bits)
    result["code"] = video_code.code

    if opts.video_include_fingerprint:
        result["fingerprint"] = base64.b64encode(signature).decode("ascii")

    do_preview = (
        opts.all_preview if isinstance(opts.all_preview, bool) else opts.video_preview
    )

    if do_preview:
        img_raw = video.extract_video_preview(uri)
        result["preview"] = image.encode_image_to_data_uri(img_raw)

    if not granular:
        return result

    if opts.video_scenes:
        if not opts.video_scenes_ffmpeg:
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

    :param Readable data: File, filepath or raw data used for Data-Code creation.
    :key int data_avg_chunk_size: Target chunk size in bytes for data chunking.
    :key int data_granular: Return granular features (one hash per chunk).
    :key int data_granular_factor: Size of granular data chunks times average chunk size.
    :key int io_chunk_size: Number of bytes to read per IO operation.
    :return: DataCode conformant dictionary
    :rtype: dict
    """

    opts = Options(**options)
    stream = uread.open_data(data)

    hasher = iscc_core.DataHasherV0()
    data = stream.read(opts.io_chunk_size)

    while data:
        hasher.push(data)
        data = stream.read(opts.io_chunk_size)

    code = hasher.code(bits=opts.data_bits)
    result = dict(code=code)

    granular = (
        opts.all_granular if isinstance(opts.all_granular, bool) else opts.data_granular
    )

    if granular:
        features = encode_data_features(hasher.chunk_sizes, hasher.chunk_features)
        result["features"] = features

    return result


def code_instance(data, **options):
    # type: (Readable, **Any) -> dict
    """Create ISCC Instance-Code.

    The Instance-Code is prefix of a cryptographic hash (blake3) of the input data.
    It´s purpose is to serve as an checksum that detects even minimal changes
    to the data of the referenced media asset. For cryptographicaly secure integrity
    checking a full 256-bit blake3 hash is provided with the `datahash` field.

    :param Readable data: File, filepath or raw data used for Instance-Code creation.
    :key int instance_bits: Length of generated Instance-Code in bits (default 64).
    :key int io_chunk_size: Number of bytes to read per IO operation.
    :return: An InstanceCode conformant dict with attributes: code, datahash, filesize
    :rtype: dict
    """
    opts = Options(**options)
    stream = uread.open_data(data)
    code = iscc_core.gen_instance_code_v0(stream, opts.instance_bits)
    return code.dict()


def code_short_id(chain, iscc_code, counter=0):
    # type: (iscc.ST_SID, str, int) -> str
    """Create an ISCC Short-ID."""
    assert chain in list(iscc.ST_SID)
    components = iscc.decompose(iscc_code)
    if len(components) > 1:
        digests = [c.bytes[:8] for c in components if c.maintype != iscc.MT.INSTANCE]
    else:
        digests = components[0].bytes[:8]

    short_id_body = iscc.similarity_hash(digests)
    n_bits_counter = 0
    if counter:
        n_bytes_counter = (counter.bit_length() + 7) // 8
        short_id_body += counter.to_bytes(n_bytes_counter, "big", signed=False)
        n_bits_counter += n_bytes_counter * 8

    code = iscc.Code((iscc.MT.SID, chain, iscc.VS.V0, n_bits_counter, short_id_body))
    return code.code
