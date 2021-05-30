# -*- coding: utf-8 -*-
"""Content-ID Image functions"""
import base64
from collections import defaultdict
import io
import pyexiv2
from loguru import logger
from pathlib import Path
from typing import Any, List, Optional, Union
import math
from statistics import median
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
from more_itertools import chunked
import iscc
from iscc.schema import FeatureType, Options, Readable
from iscc.simhash import similarity_hash
from iscc.text import normalize_text
from iscc import uread
import cv2 as cv


IMAGE_META_MAP = {
    "Xmp.dc.title": "title",
    "Xmp.dc.identifier": "identifier",
    "Xmp.dc.language": "language",
    "Xmp.xmp.Identifier": "identifier",
    "Xmp.xmp.Nickname": "title",
    "Xmp.xmpDM.shotName": "title",
    "Xmp.photoshop.Headline": "title",
    "Xmp.iptcExt.AOTitle": "title",
    "Iptc.Application2.Headline": "title",
    "Iptc.Application2.Language": "language",
    "Exif.Image.ImageID": "identifier",
    "Exif.Image.XPTitle": "title",
    "Exif.Photo.ImageUniqueID": "identifier",
}


def extract_image_metadata(data):
    # type: (Readable) -> Optional[dict]
    """Extracts and normalizes seed netadata from image files (exif, iptc, xmp).

    TODO: Create a more advanced cross-standard metadata mapping.
    Returns an optional dictionary with the following possible fields:
        - title
        - identifier
        - langauge
    """
    file = uread.open_data(data)
    try:
        img_obj = pyexiv2.ImageData(file.read())
        meta = {}
        meta.update(img_obj.read_exif())
        meta.update(img_obj.read_iptc())
        meta.update(img_obj.read_xmp())
    except Exception as e:
        logger.warning(f"Image metadata extraction failed: {e}")
        return None

    selected_meta = defaultdict(set)
    for k, v in meta.items():
        if k not in IMAGE_META_MAP:
            continue
        if isinstance(v, list):
            v = tuple(normalize_text(item) for item in v)
            if not v:
                continue
            v = ";".join(v)
            v = v.replace('lang="xdefault"', "").strip()
        elif isinstance(v, str):
            v = normalize_text(v)
            v = v.replace('lang="xdefault"', "").strip()
            if not v:
                continue
        else:
            raise ValueError(f"missed type {type(v)}")

        field = IMAGE_META_MAP[k]
        selected_meta[field].add(v)

    longest_meta = {}
    for k, v in selected_meta.items():
        # value is a set of candidates
        best_v = max(selected_meta[k], key=len)
        if not best_v:
            continue
        longest_meta[k] = best_v
    return longest_meta or None


def extract_image_features(data, n=32):
    # type: (Readable, int) -> dict
    """Extract granular features from image.

    Returns a dict (features, positions, sizes) where:
        features - base64 encoded feature hashes
        sizes - keypoint sizes as percentage relative to the larger side of the image
        positions - percentage based x, y coordinates of the corresponding keypoints
    """

    file = uread.open_data(data)
    img_array = np.array(bytearray(file.read()), dtype=np.uint8)
    img = cv.imdecode(img_array, cv.IMREAD_GRAYSCALE)

    height, width = img.shape[:2]
    pix_count = max(img.shape[:2])  # pix count of longer side
    orb = cv.ORB_create(32)
    keypoints = orb.detect(img, None)
    beblid = cv.xfeatures2d.BEBLID_create(0.75)
    keypoints, descriptors = beblid.compute(img, keypoints)
    zipped = list(zip(keypoints, descriptors))
    ranked = sorted(zipped, key=lambda x: x[0].response, reverse=True)
    feat_map = {}  # simhash -> (size, pos)
    for kp, desc in ranked:
        shash = iscc.encode_base64(
            similarity_hash([bytes(c) for c in chunked(desc, 8)])
        )
        feature_size = round(kp.size / pix_count * 100, 3)
        feature_pos = (
            round(kp.pt[0] / width * 100, 3),
            round(kp.pt[1] / height * 100, 3),
        )
        feat_map[shash] = (feature_size, feature_pos)
        if len(feat_map) == n:
            break
    features = list(feat_map.keys())
    sizes = [fm[0] for fm in feat_map.values()]
    positions = [fm[1] for fm in feat_map.values()]
    return dict(
        kind=FeatureType.image.value,
        version=0,
        features=features,
        sizes=sizes,
        positions=positions,
    )


def extract_image_preview(img, **options):
    # type: (Union[str, Path, Image.Image], **Any) -> Image.Image
    """Create a thumbnail for an image."""
    opts = Options(**options)
    size = opts.image_preview_size
    if not isinstance(img, Image.Image):
        img = Image.open(img)
    else:
        # Pillow thumbnail operates inplace - avoid side effects.
        img = img.copy()
    img.thumbnail((size, size), resample=Image.LANCZOS)
    return ImageEnhance.Sharpness(img.convert("RGB")).enhance(1.4)


def encode_image_to_data_uri(img, **options):
    # type: (Union[str, Path, Image.Image, bytes, io.BytesIO], **Any) -> str
    """Converts image to WebP data-uri."""
    opts = Options(**options)
    quality = opts.image_preview_quality

    if isinstance(img, bytes):
        img = io.BytesIO(img)

    if not isinstance(img, Image.Image):
        img = Image.open(img)

    raw = io.BytesIO()
    img.save(raw, format="WEBP", lossless=False, quality=quality, method=6)
    raw.seek(0)
    enc = base64.b64encode(raw.read()).decode("ascii")
    return "data:image/webp;base64," + enc


def trim_image(img):
    # type: (Union[str, Path, Image.Image]) -> Image.Image
    """Trim uniform colored (empty) border."""

    if not isinstance(img, Image.Image):
        img = Image.open(img)

    bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff)
    bbox = diff.getbbox()
    if bbox:
        logger.debug(f"Image has been trimmed: {img}")
        return img.crop(bbox)
    return img


def hash_image(img):
    # type: (Union[Readable, Image.Image]) -> str
    """Create hex coded image hash."""
    pixels = normalize_image(img)
    return hash_image_pixels(pixels).hex()


def normalize_image(img):
    # type: (Union[str, Path, Image.Image]) -> List[List[int]]
    """Takes a path or PIL Image Object and returns a normalized array of pixels."""

    if not isinstance(img, Image.Image):
        img = Image.open(io.BytesIO(uread.open_data(img).read()))

    if img.mode == "RGBA":
        # Add white background to images that have an alpha transparency channel
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])  # 3 is alpha channel
        img = bg

    # 1. Convert to greyscale
    img = img.convert("L")

    # 2. Resize to 32x32
    img = img.resize((32, 32), Image.BICUBIC)

    # 3. Create two dimensional array
    pixels = np.array(img).tolist()

    return pixels


def hash_image_pixels(pixels):
    # type: (List[List[int]]) -> bytes
    """Calculate image hash from 2D-Array of normalized image."""

    # 1. DCT per row
    dct_row_lists = []
    for pixel_list in pixels:
        dct_row_lists.append(compute_image_dct(pixel_list))

    # 2. DCT per col
    dct_row_lists_t = list(map(list, zip(*dct_row_lists)))
    dct_col_lists_t = []
    for dct_list in dct_row_lists_t:
        dct_col_lists_t.append(compute_image_dct(dct_list))

    dct_lists = list(map(list, zip(*dct_col_lists_t)))

    # 3. Extract upper left 8x8 corner
    flat_list = [x for sublist in dct_lists[:8] for x in sublist[:8]]

    # 4. Calculate median
    med = median(flat_list)

    # 5. Create 64-bit digest by comparing to median
    bitstring = ""
    for value in flat_list:
        if value > med:
            bitstring += "1"
        else:
            bitstring += "0"
    hash_digest = int(bitstring, 2).to_bytes(8, "big", signed=False)

    return hash_digest


def compute_image_dct(values_list):
    """
    Discrete cosine transform algorithm by Project Nayuki. (MIT License)
    See: https://www.nayuki.io/page/fast-discrete-cosine-transform-algorithms
    """

    n = len(values_list)
    if n == 1:
        return list(values_list)
    elif n == 0 or n % 2 != 0:
        raise ValueError()
    else:
        half = n // 2
        alpha = [(values_list[i] + values_list[-(i + 1)]) for i in range(half)]
        beta = [
            (values_list[i] - values_list[-(i + 1)])
            / (math.cos((i + 0.5) * math.pi / n) * 2.0)
            for i in range(half)
        ]
        alpha = compute_image_dct(alpha)
        beta = compute_image_dct(beta)
        result = []
        for i in range(half - 1):
            result.append(alpha[i])
            result.append(beta[i] + beta[i + 1])
        result.append(alpha[-1])
        result.append(beta[-1])
        return result
