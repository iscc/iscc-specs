# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
from typing import BinaryIO, List, Optional, Union
from PIL import Image
import xxhash
from blake3 import blake3
from more_itertools import windowed
from iscc.minhash import minhash_256
from iscc.image import image_hash, image_normalize
from iscc.text import text_hash, text_normalize, text_trim
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
)
from iscc.simhash import similarity_hash
from iscc.meta import meta_hash
from iscc.schema import Opts

###############################################################################
# Top-Level functions for generating ISCCs                                    #
###############################################################################


def meta_id(title, extra="", opts=None):
    # type: (Union[str, bytes], Optional[Union[str, bytes]], Optional[Union[Opts, dict]) -> dict
    """Generate Meta Code from title and extra metadata"""
    opts = Opts(**opts) if opts else Opts()
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


def content_id_text(text, bits=64):
    # type: (Union[str, bytes], int) -> str

    text = text_normalize(text)
    th = text_hash(text)
    header = write_header(MT.CONTENT, ST_CC.TEXT, VS.V0, bits)
    code = encode_base32(header + th[: bits // 8])

    return code


def content_id_image(img, bits=64):
    # type: (Union[str, BytesIO, Image.Image], int) -> str

    pixels = image_normalize(img)
    hash_digest = image_hash(pixels)
    header = write_header(MT.CONTENT, ST_CC.IMAGE, VS.V0, bits)
    code = encode_base32(header + hash_digest)
    return code


def content_id_audio(features, bits=64):
    # type: (List[int], int) -> str
    digests = []

    for int_features in windowed(features, 8, fillvalue=0):
        digest = b""
        for int_feature in int_features:
            digest += int_feature.to_bytes(4, "big", signed=True)
        digests.append(digest)
    shash_digest = similarity_hash(digests)
    n_bytes = bits // 8
    header = write_header(MT.CONTENT, ST_CC.AUDIO, VS.V0, bits)
    code = encode_base32(header + shash_digest[:n_bytes])
    return code


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
