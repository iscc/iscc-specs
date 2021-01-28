# -*- coding: utf-8 -*-
import pytest

from iscc.codec import Code
from iscc.core import content_id_text
from iscc.text import *
from iscc.metrics import distance, distance_hex
from fauxfactory.factories.strings import gen_utf8


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


def test_content_id_text_empty():
    r64 = content_id_text("")
    assert r64 == dict(code="EAASL4F2WZY7KBXB", characters=0)
    r128 = content_id_text("", text_bits=128)
    assert r128 == dict(code="EABSL4F2WZY7KBXBYUZPREWZ26IXU", characters=0)

    with pytest.raises(AssertionError):
        distance(r64["code"], r128["code"])

    assert distance(Code(r64["code"]), Code(r128["code"]), mixed=True) == 0


def test_content_id_text_default():
    a = content_id_text(TEXT_A)
    assert a == {"characters": 291, "code": "EAAR7BVKOFMBVNE4", "language": "en"}
    b = content_id_text(TEXT_B)
    assert b == {"characters": 289, "code": "EAAR7BVKOFMBVNGM", "language": "en"}
    assert distance(a["code"], b["code"]) == 2


def test_content_id_text_granular():
    a = content_id_text(TEXT_A, text_granular=True, text_avg_chunk_size=100)
    assert a == {
        "characters": 291,
        "code": "EAAR7BVKOFMBVNE4",
        "features": {
            "features": ["XYy_cVAdfP8", "7LaIeVSCsaA", "_pZVWTpBYOY", "kSem2vF2HOo"],
            "sizes": [78, 91, 66, 56],
        },
        "language": "en",
    }
    b = content_id_text(TEXT_B, text_granular=True, text_avg_chunk_size=100)
    assert b == {
        "characters": 289,
        "code": "EAAR7BVKOFMBVNGM",
        "features": {
            "features": ["XY29cVA9fO4", "7LaIeVSCsaA", "_pZVWTpBYOY", "kSem2vF2HOo"],
            "sizes": [76, 91, 66, 56],
        },
        "language": "en",
    }
    assert distance(a["code"], b["code"]) == 2


def test_text_hash():
    a = text_hash(TEXT_A).hex()
    b = text_hash(TEXT_B).hex()
    c = text_hash(TEXT_C).hex()
    assert a == "1f869a735c10bf9c32107ab4114e13d2bf93614cda99513ee9f989faf3d6983f"
    assert b == "1f869a735c18bfcc32107ab4114e13d2bf9b614cda91513ee9f189faf3d6987f"
    assert c == "366f2f1b08ba65efbbb48acf4b9953d144be674fa0af8802e7a6f1769b19c576"
    assert distance_hex(a, b) == 7


def test_text_features():
    result = text_features(TEXT_A, text_avg_chunk_size=64, text_ngram_size=13)
    assert sum(result["sizes"]) == len(TEXT_A)
    assert result == {
        "features": [
            "Ha83PFApXsU",
            "tJCNM3GDmqo",
            "ybOgbVaQd6w",
            "j97uHe9D0AY",
            "saWu27FmmP4",
            "fCr9n6iDBWo",
        ],
        "sizes": [88, 43, 52, 70, 41, 20],
    }

    result = text_features(TEXT_B, text_avg_chunk_size=64, text_ngram_size=13)
    assert sum(result["sizes"]) == len(TEXT_B)
    assert result == {
        "features": [
            "XOS48cKcoeg",
            "nYc2flAhXsU",
            "tJCNM3GDmqo",
            "ybOgbVaQd6w",
            "j97uHe9D0AY",
            "saWu27FmmP4",
            "fCr9n6iDBWo",
        ],
        "sizes": [20, 66, 43, 52, 70, 41, 20],
    }


def test_text_chunks():
    txt = gen_utf8(1024 * 100)
    chunks = list(text_chunks(txt, text_avg_chunk_size=1024))
    assert "".join(chunks) == txt


def test_trim_text():
    multibyte_2 = "ü" * 128
    trimmed = text_trim(multibyte_2, 128)
    assert 64 == len(trimmed)
    assert 128 == len(trimmed.encode("utf-8"))

    multibyte_3 = "驩" * 128
    trimmed = text_trim(multibyte_3, 128)
    assert 42 == len(trimmed)
    assert 126 == len(trimmed.encode("utf-8"))

    mixed = "Iñtërnâtiônàlizætiøn☃💩" * 6
    trimmed = text_trim(mixed, 128)
    assert 85 == len(trimmed)
    assert 128 == len(trimmed.encode("utf-8"))


def test_text_normalize():
    txt = "  Iñtërnâtiôn\nàlizætiøn☃💩 –  is a tric\t ky \u00A0 thing!\r"

    normalized = text_normalize(txt)
    assert normalized == "internation alizætiøn☃💩 is a tric ky thing!"

    assert text_normalize(" ") == ""
    assert text_normalize("  Hello  World ? ") == "hello world ?"
    assert text_normalize("Hello\nWorld") == "hello world"
