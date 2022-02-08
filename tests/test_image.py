# -*- coding: utf-8 -*-
import math
import pytest
import iscc
import iscc.image
from iscc_samples import images
from iscc_core.codec import Code
from iscc_core.code_content_image import soft_hash_image_v0
from iscc.schema import Features
from tests.test_readables import image_readables
from PIL import Image
import pathlib


HERE = pathlib.Path(__file__).parent.absolute()
IMG_ALPHA = HERE / "alpha.png"


def test_normalize_image_default():
    img = Image.open(images()[0].as_posix())
    pixels = iscc.image.normalize_image(img)
    assert len(pixels) == 1024
    assert pixels[0] == 23
    assert pixels[-1] == 51
    assert (
        soft_hash_image_v0(pixels, bits=256).hex()
        == "c343309e3c9e8e678687613c793c1ccf43309e3c9e8e65ce87613c793c1ccb8d"
    )


def test_normalize_image_opts_true():
    imo = Image.open(IMG_ALPHA)
    pixels = iscc.image.normalize_image(
        imo, image_transpose=True, image_trim=True, image_fill=True
    )
    assert (
        soft_hash_image_v0(pixels, bits=256).hex()
        == "f165ce9b3464c319e3cb9c3669c9863267ce9b3466c3191ccb9c3669cd863239"
    )


def test_normalize_image_opts_false():
    imo = Image.open(IMG_ALPHA)
    pixels = iscc.image.normalize_image(
        imo, image_transpose=False, image_trim=False, image_fill=False
    )
    # Note: transparency is rendered black by default so this creates an all black img.
    assert (
        soft_hash_image_v0(pixels, bits=256).hex()
        == "0000000000000000000000000000000000000000000000000000000000000000"
    )


def test_code_image_plain():
    assert iscc.code_image(
        images()[0], image_preview=False, image_granular=False
    ) == dict(
        iscc="EEA4GQZQTY6J5DTH",
        width=200,
        height=133,
    )


def test_code_image_global_preview_overrides():
    r = iscc.code_image(
        images()[0], all_preview=False, image_preview=True, image_granular=False
    )
    assert "preview" not in r


@pytest.mark.optional
def test_code_image_granular():
    assert iscc.code_image(images()[0], image_preview=False, image_granular=True) == {
        "iscc": "EEA4GQZQTY6J5DTH",
        "features": {
            "features": [
                "LX_6ZHK_v84",
                "ab79w3Lb-3Y",
                "FVfv7v_vePo",
                "-f9Oe-nrr98",
                "_dfa63rtqjA",
                "9__fpqXolZQ",
                "Xf6P7q_4-9M",
                "OAiKKhQWY2w",
                "XfnMv-j1oVI",
                "Kr8MIe5yogs",
                "2dwt-uPtyVo",
                "6f2q_m7UrVo",
                "9__u6_7l-2I",
                "o_8nXM1-m8Y",
                "vP_me9xsr28",
                "7fyjYPh9uVM",
                "Y_9goKj8-wM",
                "y-sYG2TW_jM",
                "Jat8cuBzsaA",
                "st4wUarm0rI",
                "mZa337yWn18",
                "97ZlKUM20T4",
                "TJoQQKEE-ws",
                "O3yfqMDwMVc",
            ],
            "kind": "image",
            "positions": [
                (37.5, 45.865),
                (37.2, 46.015),
                (37.44, 46.556),
                (39.0, 45.865),
                (39.0, 46.015),
                (61.0, 40.602),
                (38.88, 47.639),
                (30.0, 72.18),
                (39.0, 47.82),
                (51.0, 69.925),
                (38.88, 46.773),
                (42.48, 50.887),
                (37.152, 46.773),
                (50.0, 38.346),
                (39.0, 48.12),
                (42.6, 50.526),
                (42.336, 51.97),
                (58.32, 42.226),
                (41.472, 55.868),
                (49.8, 37.895),
                (35.4, 45.113),
                (56.88, 51.97),
                (54.95, 48.332),
                (58.061, 48.332),
            ],
            "sizes": [
                15.5,
                18.6,
                22.32,
                15.5,
                18.6,
                15.5,
                22.32,
                15.5,
                18.6,
                15.5,
                26.784,
                22.32,
                26.784,
                15.5,
                15.5,
                18.6,
                26.784,
                22.32,
                26.784,
                18.6,
                18.6,
                22.32,
                32.141,
                32.141,
            ],
            "version": 0,
        },
        "height": 133,
        "width": 200,
    }


def test_code_image_with_meta():
    assert iscc.code_image(
        images()[2], image_preview=False, image_granular=False
    ) == dict(
        iscc="EEA4GQZQTY6J5DTH",
        title="Concentrated Cat",
        width=200,
        height=133,
    )


def test_code_image_bits32():
    cidi32 = iscc.code_image(
        images()[0], image_bits=32, image_preview=False, image_granular=False
    )
    assert cidi32 == dict(iscc="EEAMGQZQTY", width=200, height=133)
    c1 = Code(cidi32["iscc"])
    assert c1.length == 32
    cidi64 = iscc.code_image(
        images()[0], image_bits=32, image_preview=False, image_granular=False
    )
    c2 = Code(cidi64["iscc"])
    assert c1 ^ c2 == 0


def test_code_image_preview():
    cidi = iscc.code_image(images()[0], image_preview=True, image_granular=False)
    preview = cidi["preview"]
    assert preview.startswith("data:image/webp;base64,UklGRhgIAABXRUJQVlA4IAwIAABQJQCd")
    assert preview.endswith("qSUQvbU+gC4ShEuIP+R7+yyFAjDVUbFMfQod4cLwg7wmO7EgOWgAAAA==")


def test_extract_image_metadata():
    assert iscc.image.extract_image_metadata(images()[0].as_posix()) is None
    assert iscc.image.extract_image_metadata(images()[2].as_posix()) == {
        "title": "Concentrated Cat"
    }


def test_extract_image_metadata_readables():
    for readable in image_readables():
        assert iscc.image.extract_image_metadata(readable) == {
            "title": "Concentrated Cat"
        }


def test_pi():
    """Check assumption that PI has expected value on system"""
    assert math.pi == 3.141592653589793


@pytest.mark.optional
def test_extract_image_features_readables():
    for r in image_readables():
        fo = Features(**iscc.image.extract_image_features(r))
        assert fo.features[0] == "7XzuZHrfv-w"
        assert fo.sizes[0] == 15.5
        # assert fo.positions[0] == (37.5, 45.865)
        assert fo.features[-1] == "O3yfqMDwMVc"
        assert fo.sizes[-1] == 32.141
        # assert fo.positions[-1] == (58.061, 48.332)
