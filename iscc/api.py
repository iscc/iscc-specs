# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
import gzip
import os.path
import iscc_core
from os.path import basename
import base64
import io
import mobi
from codetiming import Timer
from humanize import naturalsize
from iscc_core.code_data import DataHasherV0
from iscc_core.codec import AnyISCC
from loguru import logger as log
from typing import List, Union, Any
from PIL import Image
from blake3 import blake3
import iscc
from iscc import jcs
from iscc.mp7 import read_ffmpeg_signature
from iscc.schema import (
    GMT,
    Uri,
    Data,
    File,
    Readable,
    ISCC,
)
from iscc.options import SdkOptions, sdk_opts
from iscc.mediatype import mime_guess, mime_to_gmt
from iscc import uread
from iscc.wrappers import decompose
from iscc_core import codec


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
    opts = SdkOptions(**options) if options else sdk_opts
    result = {"version": "0-0-0"}
    features = []

    file_obj = uread.open_data(uri)

    file_name = getattr(file_obj, "name", None)
    if file_name:
        result["filename"] = basename(file_name)

    with Timer(text="{:0.4f}s for instance code creation", logger=log.debug):
        instance = code_instance(file_obj, **options)
    result.update(instance)

    with Timer(text="{:0.4f}s for data code creation", logger=log.debug):
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
        title = iscc.text.title_from_uri(file_name)

    meta = code_meta(title, extra, **options)
    result.update(meta)

    iscc_code_obj = iscc_core.gen_iscc_code_v0(
        [meta["iscc"], content["iscc"], data["iscc"], instance["iscc"]]
    ).code_obj
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
    opts = SdkOptions(**options) if options else sdk_opts
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
        with Timer(text="{:0.4f}s for content code text creation", logger=log.debug):
            cc = code_text(data, **options)
    elif gmt == GMT.image:
        with Timer(text="{:0.4f}s for content code image creation", logger=log.debug):
            cc = code_image(data, **options)
    elif gmt == GMT.audio:
        with Timer(text="{:0.4f}s for content code audio creation", logger=log.debug):
            cc = code_audio(data, **options)
    elif gmt == GMT.video:
        with Timer(text="{:0.4f}s for content code video creation", logger=log.debug):
            cc = code_video(data, **options)
    else:
        raise ValueError("Unsupported mediatype: {}".format(mediatype))

    cc["mediatype"] = mediatype
    cc["gmt"] = gmt

    return cc


def code_text(data, **options):
    # type: (Readable, **Any) -> dict
    """Generate Content-Code Text

    :param data: Any kind of text document
    """
    opts = SdkOptions(**options) if options else sdk_opts
    result = {}

    with Timer(text="{:0.4f}s for text extraction", logger=log.debug):
        text_raw = iscc.text.extract_text(data, **options)
    with Timer(text="{:0.4f}s for text metadata extraction", logger=log.debug):
        metadata = iscc.text.extract_text_metadata(data, text_raw, **options)
    result.update(metadata)

    with Timer(text="{:0.4f}s for text normalization", logger=log.debug):
        text_norm = iscc.text.normalize_text(text_raw)
    with Timer(text="{:0.4f}s for text hashing", logger=log.debug):
        digest_256 = iscc_core.code_content_text.soft_hash_text_v0(text_norm.lower())

    text_code = iscc_core.codec.encode_component(
        mtype=iscc_core.codec.MT.CONTENT,
        stype=iscc_core.codec.ST_CC.TEXT,
        version=codec.VS.V0,
        length=opts.text_bits,
        digest=digest_256,
    )
    result["iscc"] = text_code

    granular = (
        opts.all_granular if isinstance(opts.all_granular, bool) else opts.text_granular
    )
    if granular:
        with Timer(
            text="{:0.4f}s for text granular feature extraction", logger=log.debug
        ):
            features = iscc.text.extract_text_features(text_norm, **options)
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
    opts = SdkOptions(**options) if options else sdk_opts

    try:
        with Timer(text="{:0.4f}s for image metadata extraction", logger=log.debug):
            result = iscc.image.extract_image_metadata(data) or {}
    except Exception as e:
        log.error(f"Failed image metadata extraction: {e}")
        result = {}

    stream = uread.open_data(data)
    imo = Image.open(stream)
    with Timer(text="{:0.4f}s for image normalization", logger=log.debug):
        pixels = iscc.image.normalize_image(imo, **options)
    with Timer(text="{:0.4f}s for image hashing", logger=log.debug):
        image_code = iscc_core.gen_image_code_v0(pixels, bits=opts.image_bits)
    # TODO: move this to .extract_image_metadata
    image_code.width, image_code.height = imo.size
    result.update(image_code.dict(exclude_unset=True))

    if isinstance(data, Image.Image):
        img_obj = data
    else:
        img_obj = Image.open(io.BytesIO(uread.open_data(data).read()))

    granular = (
        opts.all_granular
        if isinstance(opts.all_granular, bool)
        else opts.image_granular
    )
    if granular:
        try:
            with Timer(
                text="{:0.4f}s for image granular feature extraction", logger=log.debug
            ):
                feat_obj = iscc.image.extract_image_features(
                    data, n=opts.image_granular_n
                )
            result["features"] = feat_obj
        except Exception as e:
            log.error("image feature extraction failed")
            log.exception(e)

    do_preview = (
        opts.all_preview if isinstance(opts.all_preview, bool) else opts.image_preview
    )

    if do_preview:
        with Timer(text="{:0.4f}s for image preview extraction", logger=log.debug):
            preview = iscc.image.extract_image_preview(img_obj, **options)
            preview_uri = iscc.image.encode_image_to_data_uri(preview, **options)
        result["preview"] = preview_uri

    return result


def code_audio(data, **options):
    # type: (Union[Uri, Data, List], **Any) -> dict
    """Generate Audio-ID from file(path) or Chromaprint features"""
    opts = SdkOptions(**options) if options else sdk_opts
    result = dict()

    if isinstance(data, list):
        chroma = dict(fingerprint=data)
    else:
        with Timer(text="{:0.4f}s for audio feature extraction", logger=log.debug):
            chroma = iscc.audio.extract_audio_features(data, **options)
        with Timer(text="{:0.4f}s for audio metadata extraction", logger=log.debug):
            metadata = iscc.audio.extract_audio_metadata(data)
        result.update(metadata)

    with Timer(text="{:0.4f}s for audio hashing", logger=log.debug):
        audio_code = iscc_core.gen_audio_code_v0(
            cv=chroma["fingerprint"], bits=opts.audio_bits
        )
    granular = (
        opts.all_granular
        if isinstance(opts.all_granular, bool)
        else opts.audio_granular
    )
    if granular:
        with Timer(
            text="{:0.4f}s for audio granular feature encoding", logger=log.debug
        ):
            features = iscc.audio.encode_audio_features(chroma["fingerprint"])
        result["features"] = features

    result["iscc"] = audio_code.iscc
    return result


def code_video(uri, **options):
    # type: (Union[Uri, File], **Any) -> dict
    """Compute Content-ID video."""
    opts = SdkOptions(**options) if options else sdk_opts
    result = {}
    with Timer(text="{:0.4f}s for video metadata extraction", logger=log.debug):
        metadata = iscc.video.extract_video_metadata(uri)
    result.update(metadata)

    crop_value = None
    if opts.video_crop:
        with Timer(text="{:0.4f}s for video crop detection", logger=log.debug):
            crop_value = iscc.video.detect_video_crop(uri)

    granular = (
        opts.all_granular
        if isinstance(opts.all_granular, bool)
        else opts.video_granular
    )
    do_ffmpeg_scenes = granular and opts.video_scenes_ffmpeg

    if do_ffmpeg_scenes:
        with Timer(
            text="{:0.4f}s for video signature and scene extraction", logger=log.debug
        ):
            signature, cutpoints = iscc.video.extract_video_signature_cutpoints(
                uri, crop_value, **options
            )
    else:
        with Timer(text="{:0.4f}s for video signature extraction", logger=log.debug):
            signature = iscc.video.extract_video_signature(uri, crop_value, **options)

    with Timer(text="{:0.4f}s for video signature decoding", logger=log.debug):
        frames = read_ffmpeg_signature(signature)
    log.debug(f"{naturalsize(len(signature))} video sig with {len(frames)} frames")

    with Timer(text="{:0.4f}s for video hashing", logger=log.debug):
        features = [tuple(sig.vector.tolist()) for sig in frames]
        video_code = iscc_core.gen_video_code_v0(features, bits=opts.video_bits)
    result["iscc"] = video_code.iscc

    if opts.video_include_fingerprint:
        result["fingerprint"] = base64.b64encode(signature).decode("ascii")

    do_preview = (
        opts.all_preview if isinstance(opts.all_preview, bool) else opts.video_preview
    )

    if do_preview:
        with Timer(text="{:0.4f}s for video preview extraction", logger=log.debug):
            img_raw = iscc.video.extract_video_preview(uri)
        result["preview"] = iscc.image.encode_image_to_data_uri(img_raw)

    if not granular:
        return result

    if opts.video_scenes:
        if not opts.video_scenes_ffmpeg:
            with Timer(text="{:0.4f}s for video scene detection", logger=log.debug):
                cutpoints = iscc.video.detect_video_scenes(uri, **options)
        with Timer(
            text="{:0.4f}s for video granular scene feature extraction",
            logger=log.debug,
        ):
            features = iscc.video.compute_video_features_scenes(frames, cutpoints)
    else:
        with Timer(
            text="{:0.4f}s for video granular rolling feature extraction ",
            logger=log.debug,
        ):
            features = iscc.video.compute_video_features_rolling(frames, **options)

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

    opts = SdkOptions(**options) if options else sdk_opts
    stream = uread.open_data(data)

    hasher = DataHasherV0()

    with Timer(text="{:0.4f}s for data hash", logger=log.debug):
        data = stream.read(opts.io_read_size)

        while data:
            hasher.push(data)
            data = stream.read(opts.io_read_size)

        code = hasher.code(bits=opts.data_bits)

    result = dict(iscc=code)

    granular = (
        opts.all_granular if isinstance(opts.all_granular, bool) else opts.data_granular
    )

    if granular:
        with Timer(text="{:0.4f}s for data granular feature hashing", logger=log.debug):
            features = iscc.data.encode_data_features(
                hasher.chunk_sizes, hasher.chunk_features
            )
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
    opts = SdkOptions(**options) if options else sdk_opts
    stream = uread.open_data(data)
    with Timer(text="{:0.4f}s for instance code hashing", logger=log.debug):
        code = iscc_core.gen_instance_code_v0(stream, opts.instance_bits)
    return code.dict()


def code_iscc_id(chain_id, iscc_code, uc=0):
    # type: (Union[int,codec.ST_ID], AnyISCC, int) -> dict
    """Create ISCC-ID.

    :param int chain_id: ID of chain where the ISCC registration happend.
    :param AnyISCC iscc_code: An ISCC.
    :param in uc: Uniqueness counter.
    """

    # Normalize
    components = decompose(iscc_code)
    iscc_code = iscc_core.gen_iscc_code_v0([c.code for c in components])

    return iscc_core.gen_iscc_id_v0(chain_id, iscc_code.iscc, uc).dict()
