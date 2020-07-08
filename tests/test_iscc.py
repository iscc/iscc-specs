# -*- coding: utf-8 -*-
import os
import json
import random
from io import BytesIO
import pytest
from PIL import Image, ImageFilter, ImageEnhance
from blake3 import blake3

import iscc


TESTS_PATH = os.path.dirname(os.path.realpath(__file__))
os.chdir(TESTS_PATH)


TEXT_A = u"""
    Their most significant and usefull property of similarity-preserving
    fingerprints gets lost in the fragmentation of individual, propietary and
    use case specific implementations. The real benefit lies in similarity
    preservation beyond your local data archive on a global scale accross
    vendors.
"""

TEXT_B = u"""
    The most significant and usefull property of similarity-preserving
    fingerprints gets lost in the fragmentation of individual, propietary and
    use case specific implementations. The real benefit lies in similarity
    preservation beyond your local data archive on a global scale accross
    vendors.
"""

TEXT_C = u"""
    A need for open standard fingerprinting. We don´t need the best
    Fingerprinting algorithm just an accessible and widely used one.
"""


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
    mid1, _, _ = iscc.meta_id("ISCC Content Identifiers")
    assert mid1 == "CCDFPFc87MhdT"

    mid1, _, _ = iscc.meta_id(b"ISCC Content Identifiers")
    assert mid1 == "CCDFPFc87MhdT"

    mid1, title, extra = iscc.meta_id("Die Unendliche Geschichte")
    assert mid1 == "CCAKevDpE1eEL"
    assert title == "die unendliche geschichte"
    assert extra == ""
    mid2 = iscc.meta_id(" Die unéndlíche,  Geschichte ")[0]
    assert mid1 == mid2

    mid3 = iscc.meta_id("Die Unentliche Geschichte")[0]
    assert iscc.distance(mid1, mid3) == 8

    mid4 = iscc.meta_id("Geschichte, Die Unendliche")[0]
    assert iscc.distance(mid1, mid4) == 9

    with pytest.raises(UnicodeDecodeError):
        iscc.meta_id(b"\xc3\x28")


def test_encode():
    digest = bytes.fromhex("f7d3a5b201dc92f7a7")
    code = iscc.encode(digest[:1]) + iscc.encode(digest[1:])
    assert code == "5GcvF7s13LK2L"


def test_decode():
    code = "5GcQF7sC3iY2i"
    digest = iscc.decode(code)
    assert digest.hex() == "f7d6bd587d22a7cb6d"


def test_content_id_text():
    cid_t_np = iscc.content_id_text("")
    assert len(cid_t_np) == 13
    assert cid_t_np == "CT7A4zpmccuEv"
    cid_t_p = iscc.content_id_text("", partial=True)
    assert cid_t_p == "Ct7A4zpmccuEv"
    assert 0 == iscc.distance(cid_t_p, cid_t_np)

    cid_t_a = iscc.content_id_text(TEXT_A)
    cid_t_b = iscc.content_id_text(TEXT_B)
    assert iscc.distance(cid_t_a, cid_t_b) == 2


def test_text_normalize():
    text = "  Iñtërnâtiôn\nàlizætiøn☃💩 –  is a tric\t ky \u00A0 thing!\r"
    normalized = iscc.text_normalize(text, keep_ws=False)
    assert normalized == "internationalizætiøn☃💩isatrickything"

    normalized = iscc.text_normalize(text, keep_ws=True)
    assert normalized == "internation alizætiøn☃💩 is a tric ky thing"

    assert iscc.text_normalize(" ") == ""
    assert iscc.text_normalize("  Hello  World ? ", keep_ws=True) == "hello world"
    assert iscc.text_normalize("Hello\nWorld", keep_ws=True) == "hello world"


def test_trim_text():
    multibyte_2 = "ü" * 128
    trimmed = iscc.text_trim(multibyte_2)
    assert 64 == len(trimmed)
    assert 128 == len(trimmed.encode("utf-8"))

    multibyte_3 = "驩" * 128
    trimmed = iscc.text_trim(multibyte_3)
    assert 42 == len(trimmed)
    assert 126 == len(trimmed.encode("utf-8"))

    mixed = "Iñtërnâtiônàlizætiøn☃💩" * 6
    trimmed = iscc.text_trim(mixed)
    assert 85 == len(trimmed)
    assert 128 == len(trimmed.encode("utf-8"))


def test_sliding_window():
    assert list(iscc.sliding_window("", width=4)) == [""]
    assert list(iscc.sliding_window("A", width=4)) == ["A"]
    assert list(iscc.sliding_window("Hello", width=4)) == ["Hell", "ello"]
    words = ("lorem", "ipsum", "dolor", "sit", "amet")
    assert list(iscc.sliding_window(words, 2))[0] == ("lorem", "ipsum")


def test_similarity_hash():
    all_zero = 0b0 .to_bytes(8, "big")
    assert iscc.similarity_hash((all_zero, all_zero)) == all_zero

    all_ones = 0b11111111 .to_bytes(1, "big")
    assert iscc.similarity_hash((all_ones, all_ones)) == all_ones

    a = 0b0110 .to_bytes(1, "big")
    b = 0b1100 .to_bytes(1, "big")
    r = 0b1110 .to_bytes(1, "big")
    assert iscc.similarity_hash((a, b)) == r

    a = 0b01101001 .to_bytes(1, "big")
    b = 0b00111000 .to_bytes(1, "big")
    c = 0b11100100 .to_bytes(1, "big")
    r = 0b01101000 .to_bytes(1, "big")
    assert iscc.similarity_hash((a, b, c)) == r

    a = 0b0110100101101001 .to_bytes(2, "big")
    b = 0b0011100000111000 .to_bytes(2, "big")
    c = 0b1110010011100100 .to_bytes(2, "big")
    r = 0b0110100001101000 .to_bytes(2, "big")
    assert iscc.similarity_hash((a, b, c)) == r


def test_hamming_distance():
    a = 0b0001111
    b = 0b1000111
    assert iscc.distance(a, b) == 2

    mid1 = iscc.meta_id("Die Unendliche Geschichte", "von Michael Ende")[0]

    # Change one Character
    mid2 = iscc.meta_id("Die UnXndliche Geschichte", "von Michael Ende")[0]
    assert iscc.distance(mid1, mid2) <= 10

    # Delete one Character
    mid2 = iscc.meta_id("Die nendliche Geschichte", "von Michael Ende")[0]
    assert iscc.distance(mid1, mid2) <= 14

    # Add one Character
    mid2 = iscc.meta_id("Die UnendlicheX Geschichte", "von Michael Ende")[0]
    assert iscc.distance(mid1, mid2) <= 13

    # Add, change, delete
    mid2 = iscc.meta_id("Diex Unandlische Geschiche", "von Michael Ende")[0]
    assert iscc.distance(mid1, mid2) <= 22

    # Change Word order
    mid2 = iscc.meta_id("Unendliche Geschichte, Die", "von Michael Ende")[0]
    assert iscc.distance(mid1, mid2) <= 13

    # Totaly different
    mid2 = iscc.meta_id("Now for something different")[0]
    assert iscc.distance(mid1, mid2) >= 24


def test_content_id_mixed():
    cid_t_1 = iscc.content_id_text("Some Text")
    cid_t_2 = iscc.content_id_text("Another Text")

    cid_m = iscc.content_id_mixed([cid_t_1])
    assert cid_m == "CM3k9pp7JS7nP"

    cid_m = iscc.content_id_mixed([cid_t_1, cid_t_2])
    assert cid_m == "CM3kHkNRGvnhB"

    cid_i = iscc.content_id_image("file_image_lenna.jpg")
    cid_m = iscc.content_id_mixed([cid_t_1, cid_t_2, cid_i])
    assert cid_m == "CM3hswzATv9d3"


def test_data_id():
    did_a = iscc.data_id(b"\x00")
    assert did_a == "CDiQ3FUzdCbz9"
    random.seed(1)
    data = bytearray([random.getrandbits(8) for _ in range(1000000)])  # 1 mb
    did_a = iscc.data_id(data)
    assert did_a == "CDgxemKsy77Zj"
    data.insert(500000, 1)
    data.insert(500001, 2)
    data.insert(500002, 3)
    did_b = iscc.data_id(data)
    assert did_b == did_b
    for x in range(100):  # insert 100 bytes random noise
        data.insert(random.randint(0, 1000000), random.randint(0, 255))
    did_c = iscc.data_id(data)
    assert iscc.distance(did_a, did_c) == 1


def test_instance_id():

    zero_bytes_even = b"\x00" * 16
    iid, tail, size = iscc.instance_id(zero_bytes_even)
    assert iid == "CRfawXPpg9YBp"
    assert isinstance(tail, str)
    assert tail == "ZrmFgwsJob8e42xhRJaqTUhnCfYaCboWd"
    assert size == len(zero_bytes_even)

    ff_bytes_uneven = b"\xff" * 17
    iid, tail, size = iscc.instance_id(ff_bytes_uneven)
    assert iid == "CRD4vp2iBonAV"
    assert tail == "2m5BB7r4iEbsikGfcgrVEqCKQqAVbR4X5"
    assert size == len(ff_bytes_uneven)

    more_bytes = b"\xcc" * 66000
    iid, tail, size = iscc.instance_id(more_bytes)
    assert tail == "3b1AFYxfRDyAjAyPNMTxnnXteFe6QgZfi"
    assert iid == "CRBMtvBsphc8X"
    assert size == len(more_bytes)

    digest = iscc.decode(iid)[1:] + iscc.decode(tail)
    b3sum = blake3(more_bytes).digest()
    assert digest == b3sum


def test_data_chunks():
    with open("file_image_lenna.jpg", "rb") as infile:
        chunks1 = list(iscc.data_chunks(infile))
        infile.seek(0)
        chunks2 = list(iscc.data_chunks(infile.read()))
    assert len(chunks1) == 85
    assert len(chunks1[0]) == 438
    assert len(chunks1[-1]) == 255
    assert len(chunks2) == 85
    assert len(chunks2[0]) == 438
    assert len(chunks2[-1]) == 255


def test_content_id_image():
    cid_i = iscc.content_id_image("file_image_lenna.jpg")
    assert len(cid_i) == 13
    assert cid_i == "CYmLoqBRgV32u"

    data = BytesIO(open("file_image_lenna.jpg", "rb").read())
    cid_i = iscc.content_id_image(data, partial=True)
    assert len(cid_i) == 13
    assert cid_i == "CimLoqBRgV32u"

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


def test_pi():
    """Check that PI has expected value on systemcd """
    import math

    assert math.pi == 3.141592653589793


def test_image_normalize():
    assert iscc.image_normalize("file_image_cat.jpg") == [
        [
            25,
            18,
            14,
            15,
            25,
            79,
            91,
            91,
            106,
            68,
            109,
            100,
            99,
            93,
            74,
            69,
            58,
            51,
            52,
            72,
            152,
            159,
            130,
            81,
            94,
            81,
            90,
            78,
            50,
            20,
            24,
            26,
        ],
        [
            19,
            17,
            10,
            11,
            17,
            68,
            107,
            112,
            73,
            79,
            113,
            97,
            106,
            90,
            73,
            76,
            87,
            68,
            44,
            112,
            174,
            160,
            122,
            75,
            98,
            69,
            56,
            73,
            50,
            18,
            20,
            23,
        ],
        [
            15,
            19,
            10,
            8,
            11,
            64,
            141,
            95,
            70,
            97,
            110,
            128,
            121,
            69,
            67,
            69,
            102,
            129,
            124,
            167,
            182,
            168,
            103,
            47,
            88,
            72,
            44,
            62,
            53,
            17,
            19,
            22,
        ],
        [
            13,
            18,
            11,
            7,
            7,
            112,
            201,
            173,
            101,
            93,
            124,
            128,
            94,
            70,
            75,
            76,
            115,
            134,
            154,
            176,
            205,
            178,
            85,
            34,
            70,
            71,
            46,
            43,
            49,
            19,
            17,
            19,
        ],
        [
            13,
            17,
            12,
            6,
            7,
            107,
            188,
            214,
            184,
            98,
            91,
            101,
            86,
            84,
            79,
            83,
            108,
            121,
            138,
            177,
            213,
            188,
            53,
            31,
            36,
            50,
            49,
            36,
            40,
            20,
            16,
            19,
        ],
        [
            16,
            19,
            12,
            6,
            8,
            88,
            185,
            213,
            206,
            173,
            79,
            82,
            93,
            89,
            73,
            95,
            112,
            96,
            80,
            126,
            181,
            175,
            46,
            27,
            35,
            26,
            36,
            43,
            43,
            22,
            17,
            21,
        ],
        [
            19,
            21,
            13,
            6,
            7,
            69,
            180,
            223,
            208,
            190,
            148,
            116,
            120,
            98,
            71,
            85,
            122,
            98,
            106,
            122,
            118,
            126,
            63,
            22,
            37,
            32,
            29,
            46,
            49,
            24,
            18,
            21,
        ],
        [
            19,
            21,
            17,
            8,
            7,
            62,
            144,
            221,
            223,
            207,
            177,
            129,
            131,
            89,
            98,
            74,
            99,
            122,
            124,
            131,
            129,
            89,
            53,
            17,
            33,
            45,
            32,
            47,
            44,
            24,
            19,
            20,
        ],
        [
            20,
            23,
            18,
            9,
            6,
            53,
            97,
            193,
            221,
            215,
            200,
            154,
            130,
            111,
            100,
            93,
            103,
            144,
            129,
            106,
            106,
            69,
            45,
            22,
            25,
            39,
            34,
            50,
            41,
            23,
            21,
            22,
        ],
        [
            21,
            23,
            19,
            10,
            5,
            43,
            98,
            178,
            215,
            220,
            188,
            152,
            155,
            124,
            115,
            103,
            109,
            147,
            146,
            136,
            106,
            81,
            53,
            23,
            27,
            27,
            36,
            51,
            37,
            23,
            21,
            22,
        ],
        [
            23,
            25,
            21,
            11,
            4,
            28,
            104,
            161,
            197,
            208,
            190,
            180,
            169,
            140,
            134,
            119,
            106,
            139,
            125,
            132,
            115,
            87,
            61,
            23,
            36,
            43,
            38,
            55,
            37,
            25,
            24,
            24,
        ],
        [
            23,
            25,
            21,
            13,
            5,
            16,
            87,
            113,
            158,
            188,
            182,
            168,
            166,
            154,
            129,
            123,
            132,
            126,
            160,
            156,
            119,
            107,
            72,
            27,
            35,
            41,
            47,
            59,
            39,
            29,
            28,
            28,
        ],
        [
            24,
            24,
            20,
            15,
            7,
            6,
            75,
            128,
            161,
            172,
            175,
            153,
            167,
            169,
            133,
            94,
            154,
            126,
            114,
            97,
            102,
            83,
            75,
            31,
            32,
            39,
            50,
            71,
            42,
            31,
            29,
            29,
        ],
        [
            25,
            23,
            19,
            16,
            12,
            3,
            55,
            130,
            164,
            163,
            184,
            190,
            182,
            175,
            168,
            128,
            149,
            132,
            65,
            125,
            133,
            82,
            50,
            35,
            33,
            46,
            56,
            72,
            38,
            30,
            28,
            28,
        ],
        [
            25,
            23,
            19,
            17,
            17,
            9,
            30,
            128,
            167,
            180,
            195,
            175,
            147,
            207,
            182,
            157,
            129,
            107,
            140,
            128,
            157,
            108,
            87,
            34,
            33,
            45,
            57,
            49,
            31,
            28,
            28,
            31,
        ],
        [
            25,
            23,
            19,
            19,
            19,
            19,
            22,
            107,
            174,
            168,
            168,
            203,
            147,
            202,
            222,
            166,
            127,
            75,
            84,
            133,
            144,
            114,
            80,
            34,
            40,
            53,
            43,
            30,
            31,
            32,
            31,
            34,
        ],
        [
            25,
            21,
            20,
            23,
            28,
            26,
            19,
            80,
            146,
            133,
            210,
            162,
            198,
            151,
            224,
            175,
            128,
            90,
            137,
            173,
            103,
            82,
            56,
            38,
            55,
            61,
            33,
            27,
            36,
            39,
            34,
            34,
        ],
        [
            25,
            23,
            25,
            26,
            33,
            38,
            22,
            32,
            142,
            207,
            194,
            184,
            133,
            151,
            215,
            201,
            129,
            68,
            144,
            125,
            104,
            98,
            66,
            56,
            71,
            55,
            38,
            39,
            36,
            36,
            39,
            39,
        ],
        [
            26,
            26,
            27,
            25,
            31,
            41,
            40,
            27,
            94,
            206,
            211,
            162,
            179,
            201,
            159,
            210,
            139,
            48,
            99,
            125,
            116,
            86,
            74,
            69,
            56,
            40,
            41,
            34,
            36,
            39,
            40,
            43,
        ],
        [
            28,
            27,
            30,
            27,
            30,
            36,
            42,
            43,
            65,
            138,
            202,
            194,
            166,
            175,
            135,
            195,
            157,
            58,
            98,
            110,
            112,
            90,
            80,
            54,
            21,
            24,
            32,
            40,
            40,
            43,
            42,
            44,
        ],
        [
            26,
            27,
            37,
            29,
            30,
            34,
            36,
            43,
            39,
            100,
            198,
            222,
            216,
            208,
            182,
            181,
            172,
            86,
            110,
            130,
            125,
            108,
            101,
            49,
            25,
            30,
            34,
            41,
            44,
            47,
            45,
            45,
        ],
        [
            27,
            28,
            36,
            31,
            33,
            35,
            32,
            36,
            39,
            118,
            233,
            231,
            240,
            212,
            227,
            179,
            119,
            149,
            138,
            141,
            145,
            142,
            131,
            60,
            48,
            49,
            43,
            42,
            45,
            47,
            46,
            46,
        ],
        [
            30,
            35,
            34,
            40,
            42,
            44,
            43,
            56,
            61,
            103,
            241,
            249,
            248,
            230,
            239,
            223,
            138,
            196,
            156,
            163,
            170,
            176,
            152,
            47,
            41,
            56,
            59,
            57,
            52,
            46,
            46,
            47,
        ],
        [
            36,
            45,
            34,
            39,
            52,
            58,
            60,
            54,
            63,
            104,
            219,
            253,
            241,
            241,
            240,
            215,
            169,
            177,
            174,
            214,
            208,
            195,
            167,
            68,
            44,
            58,
            52,
            46,
            48,
            45,
            46,
            49,
        ],
        [
            46,
            51,
            38,
            39,
            46,
            53,
            62,
            75,
            98,
            104,
            137,
            208,
            199,
            181,
            220,
            214,
            180,
            109,
            123,
            241,
            236,
            214,
            163,
            60,
            58,
            48,
            61,
            55,
            49,
            44,
            47,
            50,
        ],
        [
            59,
            51,
            42,
            37,
            52,
            63,
            69,
            98,
            95,
            81,
            71,
            109,
            122,
            104,
            121,
            120,
            94,
            50,
            67,
            219,
            248,
            215,
            127,
            66,
            60,
            54,
            41,
            58,
            56,
            41,
            46,
            54,
        ],
        [
            67,
            61,
            54,
            33,
            67,
            87,
            81,
            92,
            78,
            69,
            60,
            102,
            90,
            82,
            73,
            71,
            70,
            57,
            40,
            110,
            187,
            132,
            87,
            80,
            67,
            57,
            48,
            58,
            65,
            44,
            45,
            53,
        ],
        [
            73,
            72,
            51,
            37,
            80,
            86,
            85,
            88,
            63,
            69,
            75,
            87,
            81,
            75,
            74,
            75,
            78,
            67,
            50,
            54,
            69,
            50,
            73,
            79,
            75,
            56,
            62,
            55,
            65,
            55,
            45,
            52,
        ],
        [
            77,
            71,
            40,
            51,
            77,
            73,
            91,
            85,
            54,
            78,
            90,
            71,
            83,
            73,
            75,
            72,
            77,
            74,
            59,
            56,
            66,
            49,
            66,
            74,
            61,
            57,
            68,
            63,
            54,
            61,
            53,
            51,
        ],
        [
            72,
            70,
            56,
            65,
            69,
            77,
            88,
            76,
            56,
            81,
            97,
            68,
            80,
            73,
            72,
            74,
            77,
            66,
            63,
            61,
            65,
            53,
            66,
            69,
            59,
            59,
            61,
            70,
            54,
            64,
            51,
            55,
        ],
        [
            70,
            68,
            63,
            67,
            67,
            70,
            79,
            68,
            66,
            81,
            87,
            69,
            78,
            73,
            73,
            72,
            76,
            66,
            61,
            67,
            66,
            58,
            67,
            62,
            64,
            60,
            62,
            62,
            54,
            63,
            49,
            52,
        ],
        [
            77,
            69,
            64,
            69,
            64,
            68,
            70,
            72,
            73,
            84,
            76,
            72,
            78,
            77,
            75,
            72,
            77,
            66,
            67,
            65,
            70,
            59,
            64,
            65,
            65,
            64,
            61,
            65,
            53,
            61,
            50,
            52,
        ],
    ]
