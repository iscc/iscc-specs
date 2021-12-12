# -*- coding: utf-8 -*-
"""Content-ID Image functions"""
import base64
from collections import defaultdict
import io
import pyexiv2
from iscc_core.codec import encode_base64
from loguru import logger
from pathlib import Path
from typing import Any, Optional, Sequence, Union
from PIL import Image, ImageChops, ImageEnhance, ImageOps
import numpy as np
from more_itertools import chunked
from iscc.schema import FeatureType, Readable
from iscc_core.simhash import similarity_hash
from iscc.text import normalize_text
from iscc.options import SdkOptions, sdk_opts
from iscc import uread


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
    "Iptc.Application2.ObjectName": "title",
    "Iptc.Application2.Language": "language",
    "Exif.Image.ImageID": "identifier",
    "Exif.Image.XPTitle": "title",
    "Exif.Photo.ImageUniqueID": "identifier",
}


def extract_image_metadata(data):
    # type: (Readable) -> Optional[dict]
    """Extracts and normalizes seed metadata from image files (exif, iptc, xmp).

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
        elif isinstance(v, dict):
            v = v.get('lang="x-default"', None)
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
    try:
        import cv2 as cv
    except ImportError as e:
        raise EnvironmentError(
            "Please install opencv-contrib-python-headless for granular image support"
        )

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
        shash = encode_base64(similarity_hash([bytes(c) for c in chunked(desc, 8)]))
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
    opts = SdkOptions(**options) if options else sdk_opts
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
    opts = SdkOptions(**options) if options else sdk_opts

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


def normalize_image(imo, **options):
    # type: (Image.Image, **bool) -> Sequence[int]
    """Normalize image for hash calculation.

    :param Image.Image imo: Pillow Image Object
    :key bool image_transpose: Transpose image according to EXIF Orientation
    :key bool image_fill: Add gray background to image if it has alpha transparency
    :key bool image_trim: Crop empty borders of image
    :return: Normalized and flattened image 1024-pixel array (from 32x32 gray pixels)
    :rtype: Sequence[int]
    """
    opts = SdkOptions(**options) if options else sdk_opts

    # Transpose image according to EXIF Orientation tag
    if opts.image_transpose:
        imo = transpose_image(imo)

    # Add gray background to image if it has alpha transparency
    if opts.image_fill:
        imo = fill_image(imo)

    # Trim uniform colored (empty) border if there is one
    if opts.image_trim:
        imo = trim_image(imo)

    # Convert to grayscale
    imo = imo.convert("L")

    # Resize to 32x32
    im = imo.resize((32, 32), Image.BICUBIC)

    # A flattened sequence of grayscale pixel values (1024 pixels)
    pixels = im.getdata()

    return pixels


def transpose_image(imo):
    # type: (Image.Image) -> Image.Image
    """
    Transpose image according to EXIF Orientation tag

    :param Image.Image imo: Pillow Image Object
    :return: EXIF transposed image
    :rtype: Image.Image
    """
    imo = ImageOps.exif_transpose(imo)
    logger.debug(f"Image exif transpose applied")
    return imo


def fill_image(imo):
    # type: (Image.Image) -> Image.Image
    """
    Add gray background to image if it has alpha transparency

    :param Image.Image imo: Pillow Image Object
    :return: Image where alpha transparency is replaced with gray background.
    :rtype: Image.Image
    """
    if imo.mode in ("RGBA", "LA") or (imo.mode == "P" and "transparency" in imo.info):
        if imo.mode != "RGBA":
            imo = imo.convert("RGBA")
        bg = Image.new("RGBA", imo.size, (126, 126, 126))
        imo = Image.alpha_composite(bg, imo)
        logger.debug(f"Image transparency filled with gray")
    return imo


def trim_image(imo):
    # type: (Image.Image) -> Image.Image
    """Trim uniform colored (empty) border.

    Takes the upper left pixel as reference to

    :param Image.Image imo: Pillow Image Object
    :return: Image with uniform colored (empty) border removed.
    :rtype: Image.Image
    """

    bg = Image.new(imo.mode, imo.size, imo.getpixel((0, 0)))
    diff = ImageChops.difference(imo, bg)
    diff = ImageChops.add(diff, diff)
    bbox = diff.getbbox()
    if bbox:
        logger.debug(f"Image has been trimmed")
        return imo.crop(bbox)
    return imo
