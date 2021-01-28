# -*- coding: utf-8 -*-
import os
import json
from io import BytesIO
import pytest
from PIL import Image, ImageFilter, ImageEnhance
import iscc


TESTS_PATH = os.path.dirname(os.path.realpath(__file__))
os.chdir(TESTS_PATH)


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
    mid1 = iscc.meta_id("ISCC Content Identifiers")["code"]
    assert mid1 == "AAA47ZR5JWZ6E7Q3"

    mid1 = iscc.meta_id(b"ISCC Content Identifiers")["code"]
    assert mid1 == "AAA47ZR5JWZ6E7Q3"

    mid1, title = iscc.meta_id("Die Unendliche Geschichte").values()
    assert mid1 == "AAA3DZ6UG5MYA7MF"
    assert title == "Die Unendliche Geschichte"

    mid2 = iscc.meta_id(" Die unéndlíche,  Geschichte ")["code"]
    assert mid1 != mid2

    mid3 = iscc.meta_id("Die Unentliche Geschichte")["code"]
    assert iscc.distance(mid1, mid3) == 11

    mid4 = iscc.meta_id("Geschichte, Die Unendliche")["code"]
    assert iscc.distance(mid1, mid4) == 11

    with pytest.raises(UnicodeDecodeError):
        iscc.meta_id(b"\xc3\x28")


def test_meta_id_composite():
    mid1 = iscc.meta_id("This is some Title", "")["code"]
    mid2 = iscc.meta_id("This is some Title", "And some extra metadata")["code"]
    assert iscc.decode_base32(mid1)[:5] == iscc.decode_base32(mid2)[:5]
    assert iscc.decode_base32(mid1)[5:] != iscc.decode_base32(mid2)[5:]


def test_hamming_distance():
    a = 0b0001111
    b = 0b1000111
    assert iscc.distance(a, b) == 2

    mid1 = iscc.meta_id("Die Unendliche Geschichte", "von Michael Ende")["code"]

    # Change one Character
    mid2 = iscc.meta_id("Die UnXndliche Geschichte", "von Michael Ende")["code"]
    assert iscc.distance(mid1, mid2) <= 10

    # Delete one Character
    mid2 = iscc.meta_id("Die nendliche Geschichte", "von Michael Ende")["code"]
    assert iscc.distance(mid1, mid2) <= 14

    # Add one Character
    mid2 = iscc.meta_id("Die UnendlicheX Geschichte", "von Michael Ende")["code"]
    assert iscc.distance(mid1, mid2) <= 13

    # Add, change, delete
    mid2 = iscc.meta_id("Diex Unandlische Geschiche", "von Michael Ende")["code"]
    assert iscc.distance(mid1, mid2) <= 22

    # Change Word order
    mid2 = iscc.meta_id("Unendliche Geschichte, Die", "von Michael Ende")["code"]
    assert iscc.distance(mid1, mid2) <= 13

    # Totaly different
    mid2 = iscc.meta_id("Now for something different")["code"]
    assert iscc.distance(mid1, mid2) >= 24


def test_content_id_mixed():
    cid_t_1 = iscc.content_id_text("Some Text")
    cid_t_2 = iscc.content_id_text("Another Text")

    cid_m = iscc.content_id_mixed([cid_t_1])
    assert cid_m == "EUASAAJV7U3YRWXF"

    cid_m = iscc.content_id_mixed([cid_t_1, cid_t_2])
    assert cid_m == "EUASAAJX7635T7X7"

    cid_i = iscc.content_id_image("file_image_lenna.jpg")
    cid_m = iscc.content_id_mixed([cid_t_1, cid_t_2, cid_i])
    assert cid_m == "EUASAAJVZ43AT7HT"


def test_content_id_image():
    cid_i = iscc.content_id_image("file_image_lenna.jpg")
    assert len(cid_i) == 16
    assert cid_i == "EEAZTRSWFV2THIUW"

    data = BytesIO(open("file_image_lenna.jpg", "rb").read())
    cid_i = iscc.content_id_image(data)
    assert len(cid_i) == 16
    assert cid_i == "EEAZTRSWFV2THIUW"

    img1 = Image.open("file_image_lenna.jpg")
    img2 = img1.filter(ImageFilter.GaussianBlur(10))
    img3 = ImageEnhance.Brightness(img1).enhance(1.4)
    img4 = ImageEnhance.Contrast(img1).enhance(1.2)

    cid1 = iscc.content_id_image(img1)
    cid2 = iscc.content_id_image(img2)
    cid3 = iscc.content_id_image(img3)
    cid4 = iscc.content_id_image(img4)

    assert iscc.distance(cid1, cid2) == 0
    assert iscc.distance(cid1, cid3) == 2
    assert iscc.distance(cid1, cid4) == 0
