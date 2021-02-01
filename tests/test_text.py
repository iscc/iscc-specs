# -*- coding: utf-8 -*-
import io

import pytest
from iscc.codec import Code
from iscc.core import code_text
from iscc import text
from iscc.metrics import distance, distance_hex
from fauxfactory.factories.strings import gen_utf8
from iscc_samples import texts

from tests.test_readables import text_readables


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


def test_extract_text_readables():
    for readable in text_readables():
        result = text.extract_text(readable)
        assert len(result["content"]) == 6146
        assert "title" in result["metadata"]


def test_extract_text_file():
    for tf in texts():
        result = text.extract_text(tf)
        assert isinstance(result["content"], (str, type(None)))
        assert isinstance(result["metadata"], dict)


def test_code_text_empty():
    r64 = code_text(b"")
    assert r64 == dict(code="EAASL4F2WZY7KBXB", characters=0)
    r128 = code_text(b"", text_bits=128)
    assert r128 == dict(code="EABSL4F2WZY7KBXBYUZPREWZ26IXU", characters=0)

    with pytest.raises(AssertionError):
        distance(r64["code"], r128["code"])

    assert distance(Code(r64["code"]), Code(r128["code"]), mixed=True) == 0


def test_code_text_default():
    a = code_text(TEXT_A.encode("utf-8"))
    assert a == {
        "characters": 291,
        "code": "EAAR7BVKOFMBVNE4",
        "language": "en",
        "title": "their most significant and usefull property of similaritypreserving",
    }
    b = code_text(TEXT_B.encode("utf-8"))
    assert b == {
        "characters": 289,
        "code": "EAAR7BVKOFMBVNGM",
        "language": "en",
        "title": "the most significant and usefull property of similaritypreserving",
    }
    assert distance(a["code"], b["code"]) == 2


def test_code_text_granular():
    a = code_text(TEXT_A.encode("utf-8"), text_granular=True, text_avg_chunk_size=100)
    assert a == {
        "characters": 291,
        "code": "EAAR7BVKOFMBVNE4",
        "features": {
            "features": ["XYy_cVAdfP8", "7LaIeVSCsaA", "_pZVWTpBYOY", "kSem2vF2HOo"],
            "sizes": [78, 91, 66, 56],
        },
        "language": "en",
        "title": "their most significant and usefull property of similaritypreserving",
    }
    b = code_text(TEXT_B.encode("utf-8"), text_granular=True, text_avg_chunk_size=100)
    assert b == {
        "characters": 289,
        "code": "EAAR7BVKOFMBVNGM",
        "features": {
            "features": ["XY29cVA9fO4", "7LaIeVSCsaA", "_pZVWTpBYOY", "kSem2vF2HOo"],
            "sizes": [76, 91, 66, 56],
        },
        "language": "en",
        "title": "the most significant and usefull property of similaritypreserving",
    }
    assert distance(a["code"], b["code"]) == 2


def test_hash_text():
    a = text.hash_text(TEXT_A).hex()
    b = text.hash_text(TEXT_B).hex()
    c = text.hash_text(TEXT_C).hex()
    assert a == "1f869a735c10bf9c32107ab4114e13d2bf93614cda99513ee9f989faf3d6983f"
    assert b == "1f869a735c18bfcc32107ab4114e13d2bf9b614cda91513ee9f189faf3d6987f"
    assert c == "366f2f1b08ba65efbbb48acf4b9953d144be674fa0af8802e7a6f1769b19c576"
    assert distance_hex(a, b) == 7


def test_compute_text_features():
    result = text.compute_text_features(
        TEXT_A, text_avg_chunk_size=64, text_ngram_size=13
    )
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

    result = text.compute_text_features(
        TEXT_B, text_avg_chunk_size=64, text_ngram_size=13
    )
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


def test_chunk_text():
    txt = gen_utf8(1024 * 100)
    chunks = list(text.chunk_text(txt, text_avg_chunk_size=1024))
    assert "".join(chunks) == txt


def test_trim_text():
    multibyte_2 = "ü" * 128
    trimmed = text.trim_text(multibyte_2, 128)
    assert 64 == len(trimmed)
    assert 128 == len(trimmed.encode("utf-8"))

    multibyte_3 = "驩" * 128
    trimmed = text.trim_text(multibyte_3, 128)
    assert 42 == len(trimmed)
    assert 126 == len(trimmed.encode("utf-8"))

    mixed = "Iñtërnâtiônàlizætiøn☃💩" * 6
    trimmed = text.trim_text(mixed, 128)
    assert 85 == len(trimmed)
    assert 128 == len(trimmed.encode("utf-8"))


def test_normalize_text():
    txt = "  Iñtërnâtiôn\nàlizætiøn☃💩 –  is a tric\t ky \u00A0 thing!\r"

    normalized = text.normalize_text(txt)
    assert normalized == "internation alizætiøn☃💩 is a tric ky thing!"

    assert text.normalize_text(" ") == ""
    assert text.normalize_text("  Hello  World ? ") == "hello world ?"
    assert text.normalize_text("Hello\nWorld") == "hello world"
