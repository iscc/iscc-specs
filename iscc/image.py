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
from iscc.schema import Options, Readable
from iscc.text import normalize_text
from iscc import uread


def extract_image_metadata(data):
    # type: (Readable) -> Optional[dict]
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
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        logger.debug(f"Image has been trimmed: {img}")
        return img.crop(bbox)
    return img


def normalize_image(img):
    # type: (Union[str, Path, Image.Image]) -> List[List[int]]
    """Takes a path or PIL Image Object and returns a normalized array of pixels."""

    if not isinstance(img, Image.Image):
        img = Image.open(img)

    # 1. Convert to greyscale
    img = img.convert("L")

    # 2. Resize to 32x32
    img = img.resize((32, 32), Image.BICUBIC)

    # 3. Create two dimensional array
    pixels = np.array(img).tolist()

    return pixels


def hash_image(pixels):
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
