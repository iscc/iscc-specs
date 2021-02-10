# -*- coding: utf-8 -*-
import os
import json
import pytest
from PIL import Image, ImageFilter, ImageEnhance
import iscc
from iscc.codec import decode_base32


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
    mid1 = iscc.code_meta("ISCC Content Identifiers")["code"]
    assert mid1 == "AAA47ZR5JWZ6E7Q3"

    mid1 = iscc.code_meta(b"ISCC Content Identifiers")["code"]
    assert mid1 == "AAA47ZR5JWZ6E7Q3"

    r = iscc.code_meta("Die Unendliche Geschichte")
    mid1, title = r["code"], r["title"]
    assert mid1 == "AAA3DZ6UG5MYA7MF"
    assert title == "Die Unendliche Geschichte"

    mid2 = iscc.code_meta(" Die unéndlíche,  Geschichte ")["code"]
    assert mid1 != mid2

    mid3 = iscc.code_meta("Die Unentliche Geschichte")["code"]
    assert iscc.distance(mid1, mid3) == 11

    mid4 = iscc.code_meta("Geschichte, Die Unendliche")["code"]
    assert iscc.distance(mid1, mid4) == 11

    with pytest.raises(UnicodeDecodeError):
        iscc.code_meta(b"\xc3\x28")


def test_code_meta_composite():
    mid1 = iscc.code_meta("This is some Title", "")["code"]
    mid2 = iscc.code_meta("This is some Title", "And some extra metadata")["code"]
    assert decode_base32(mid1)[:5] == decode_base32(mid2)[:5]
    assert decode_base32(mid1)[5:] != decode_base32(mid2)[5:]


def test_hamming_distance():
    a = 0b0001111
    b = 0b1000111
    assert iscc.distance(a, b) == 2

    mid1 = iscc.code_meta("Die Unendliche Geschichte", "von Michael Ende")["code"]

    # Change one Character
    mid2 = iscc.code_meta("Die UnXndliche Geschichte", "von Michael Ende")["code"]
    assert iscc.distance(mid1, mid2) <= 10

    # Delete one Character
    mid2 = iscc.code_meta("Die nendliche Geschichte", "von Michael Ende")["code"]
    assert iscc.distance(mid1, mid2) <= 14

    # Add one Character
    mid2 = iscc.code_meta("Die UnendlicheX Geschichte", "von Michael Ende")["code"]
    assert iscc.distance(mid1, mid2) <= 13

    # Add, change, delete
    mid2 = iscc.code_meta("Diex Unandlische Geschiche", "von Michael Ende")["code"]
    assert iscc.distance(mid1, mid2) <= 22

    # Change Word order
    mid2 = iscc.code_meta("Unendliche Geschichte, Die", "von Michael Ende")["code"]
    assert iscc.distance(mid1, mid2) <= 13

    # Totaly different
    mid2 = iscc.code_meta("Now for something different")["code"]
    assert iscc.distance(mid1, mid2) >= 24


def test_content_id_image():
    cid_i = iscc.code_image("file_image_lenna.jpg")
    assert len(cid_i["code"]) == 16
    assert cid_i == {"code": "EEAZTRSWFV2THIUW", "height": 512, "width": 512}

    data = open("file_image_lenna.jpg", "rb").read()
    cid_i = iscc.code_image(data)
    assert len(cid_i["code"]) == 16
    assert cid_i == {"code": "EEAZTRSWFV2THIUW", "height": 512, "width": 512}

    img1 = Image.open("file_image_lenna.jpg")
    img2 = img1.filter(ImageFilter.GaussianBlur(10))
    img3 = ImageEnhance.Brightness(img1).enhance(1.4)
    img4 = ImageEnhance.Contrast(img1).enhance(1.2)

    cid1 = iscc.code_image(img1)["code"]
    cid2 = iscc.code_image(img2)["code"]
    cid3 = iscc.code_image(img3)["code"]
    cid4 = iscc.code_image(img4)["code"]

    assert iscc.distance(cid1, cid2) == 0
    assert iscc.distance(cid1, cid3) == 2
    assert iscc.distance(cid1, cid4) == 0
