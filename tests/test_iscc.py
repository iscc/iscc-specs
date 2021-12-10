# -*- coding: utf-8 -*-
import io
import os
import json

import iscc_core
import pytest
from PIL import Image, ImageFilter, ImageEnhance
import iscc
from iscc_core.codec import decode_base32


TESTS_PATH = os.path.dirname(os.path.realpath(__file__))
os.chdir(TESTS_PATH)


def test_iscc_version():
    assert iscc.__version__.split("1.1")


def test_test_data():
    with open("test_data.json", encoding="utf-8") as jfile:
        data = json.load(jfile)
        assert type(data) == dict
        for funcname, tests in data.items():
            for testname, testdata in tests.items():
                if not testname.startswith("test_"):
                    continue
                func = getattr(iscc, funcname)
                args = testdata["inputs"]
                if funcname in ["data_chunks"]:
                    testdata["outputs"] = [
                        bytes.fromhex(i.split(":")[1]) for i in testdata["outputs"]
                    ]
                    result = list(func(*args))
                else:
                    result = func(*args)
                expected = testdata["outputs"]

                assert result == expected, "%s %s " % (funcname, args)


def test_meta_id():
    mid1 = iscc.code_meta("ISCC Content Identifiers")["iscc"]
    assert mid1 == "AAA47ZR5JWZ6E7Q3"

    mid1 = iscc.code_meta(b"ISCC Content Identifiers")["iscc"]
    assert mid1 == "AAA47ZR5JWZ6E7Q3"

    r = iscc.code_meta("Die Unendliche Geschichte")
    mid1, title = r["iscc"], r["title"]
    assert mid1 == "AAA3DZ6UG5MYA7MF"
    assert title == "Die Unendliche Geschichte"

    mid2 = iscc.code_meta(" Die unéndlíche,  Geschichte ")["iscc"]
    assert mid1 != mid2

    mid3 = iscc.code_meta("Die Unentliche Geschichte")["iscc"]
    assert iscc.distance(mid1, mid3) == 11

    mid4 = iscc.code_meta("Geschichte, Die Unendliche")["iscc"]
    assert iscc.distance(mid1, mid4) == 11

    with pytest.raises(UnicodeDecodeError):
        iscc.code_meta(b"\xc3\x28")


def test_code_meta_composite():
    mid1 = iscc.code_meta("This is some Title", "")["iscc"]
    mid2 = iscc.code_meta("This is some Title", "And some extra metadata")["iscc"]
    assert decode_base32(mid1)[:5] == decode_base32(mid2)[:5]
    assert decode_base32(mid1)[5:] != decode_base32(mid2)[5:]


def test_hamming_distance():
    a = 0b0001111
    b = 0b1000111
    assert iscc.distance(a, b) == 2

    mid1 = iscc.code_meta("Die Unendliche Geschichte", "von Michael Ende")["iscc"]

    # Change one Character
    mid2 = iscc.code_meta("Die UnXndliche Geschichte", "von Michael Ende")["iscc"]
    assert iscc.distance(mid1, mid2) <= 10

    # Delete one Character
    mid2 = iscc.code_meta("Die nendliche Geschichte", "von Michael Ende")["iscc"]
    assert iscc.distance(mid1, mid2) <= 14

    # Add one Character
    mid2 = iscc.code_meta("Die UnendlicheX Geschichte", "von Michael Ende")["iscc"]
    assert iscc.distance(mid1, mid2) <= 13

    # Add, change, delete
    mid2 = iscc.code_meta("Diex Unandlische Geschiche", "von Michael Ende")["iscc"]
    assert iscc.distance(mid1, mid2) <= 22

    # Change Word order
    mid2 = iscc.code_meta("Unendliche Geschichte, Die", "von Michael Ende")["iscc"]
    assert iscc.distance(mid1, mid2) <= 13

    # Totaly different
    mid2 = iscc.code_meta("Now for something different")["iscc"]
    assert iscc.distance(mid1, mid2) >= 24


def test_content_id_image():
    cid_i = iscc.code_image(
        "file_image_lenna.jpg", image_preview=False, image_granular=False
    )
    assert len(cid_i["iscc"]) == 16
    assert cid_i == {"iscc": "EEAZTRSWFV2THIUW", "height": 512, "width": 512}


def test_content_id_image_robust():
    data = open("file_image_lenna.jpg", "rb").read()
    cid_i = iscc.code_image(data, image_preview=False, image_granular=False)
    assert len(cid_i["iscc"]) == 16
    assert cid_i == {"iscc": "EEAZTRSWFV2THIUW", "height": 512, "width": 512}

    img1_obj = Image.open("file_image_lenna.jpg")

    img2_obj = img1_obj.filter(ImageFilter.GaussianBlur(10))
    img2 = io.BytesIO()
    img2_obj.save(img2, format="JPEG")

    img3_obj = ImageEnhance.Brightness(img1_obj).enhance(1.4)
    img3 = io.BytesIO()
    img3_obj.save(img3, format="JPEG")

    img4_obj = ImageEnhance.Contrast(img1_obj).enhance(1.2)
    img4 = io.BytesIO()
    img4_obj.save(img4, format="JPEG")

    cid1 = iscc_core.gen_image_code_v0(open("file_image_lenna.jpg", "rb"))
    cid2 = iscc_core.gen_image_code_v0(img2)
    cid3 = iscc_core.gen_image_code_v0(img3)
    cid4 = iscc_core.gen_image_code_v0(img4)

    assert iscc.distance(cid1.iscc, cid2.iscc) == 0
    assert iscc.distance(cid1.iscc, cid3.iscc) == 2
    assert iscc.distance(cid1.iscc, cid4.iscc) == 0
