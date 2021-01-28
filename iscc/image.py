# -*- coding: utf-8 -*-
"""Content-ID Image functions"""
from pathlib import Path
from typing import List, Union
import math
from statistics import median
from PIL import Image, ImageChops
import numpy as np


def image_hash(pixels):
    # type: (List[List[int]]) -> bytes
    """Calculate image hash from 2D-Array of greyscale pixels."""

    # 1. DCT per row
    dct_row_lists = []
    for pixel_list in pixels:
        dct_row_lists.append(dct(pixel_list))

    # 2. DCT per col
    dct_row_lists_t = list(map(list, zip(*dct_row_lists)))
    dct_col_lists_t = []
    for dct_list in dct_row_lists_t:
        dct_col_lists_t.append(dct(dct_list))

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


def image_normalize(img):
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


def image_trim_border(img):
    # type: (Union[str, Path, Image.Image]) -> Image.Image
    """Trim uniform colored border."""

    if not isinstance(img, Image.Image):
        img = Image.open(img)

    bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return img.crop(bbox)
    return img


def dct(values_list):
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
        alpha = dct(alpha)
        beta = dct(beta)
        result = []
        for i in range(half - 1):
            result.append(alpha[i])
            result.append(beta[i] + beta[i + 1])
        result.append(alpha[-1])
        result.append(beta[-1])
        return result
