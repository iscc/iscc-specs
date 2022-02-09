# -*- coding: utf-8 -*-
import pytest
from iscc_core import ContentCodeText

import iscc
from iscc_core.codec import Code
from fauxfactory.factories.strings import gen_utf8
from iscc_samples import texts
from tests.test_readables import text_readables
import iscc.text
import iscc.metrics


TEXT_A = """
    Their most significant and usefull property of similarity-preserving
    fingerprints gets lost in the fragmentation of individual, propietary and
    use case specific implementations. The real benefit lies in similarity
    preservation beyond your local data archive on a global scale accross
    vendors.
"""

TEXT_B = """
    The most significant and usefull property of similarity-preserving
    fingerprints gets lost in the fragmentation of individual, propietary and
    use case specific implementations. The real benefit lies in similarity
    preservation beyond your local data archive on a global scale accross
    vendors.
"""

TEXT_C = """
    A need for open standard fingerprinting. We don´t need the best
    Fingerprinting algorithm just an accessible and widely used one.
"""


def test_extract_text_readables():
    for readable in text_readables():
        if not isinstance(readable, bytearray):
            result = iscc.text.extract_text(readable)
            assert type(result) == str
            assert len(result) == 6070


def test_extract_text_filetypes():
    for tf in texts():
        if tf.suffix != ".mobi":
            result = iscc.text.extract_text(tf)
            assert isinstance(result, str)


def test_extract_text_metadata():
    src = texts()[2]
    text = iscc.text.extract_text(src)
    # Call with text
    assert iscc.text.extract_text_metadata(src, text) == {
        "characters": 292710,
        "language": "en",
        "title": "Children's Literature",
    }
    # Call without text
    assert iscc.text.extract_text_metadata(src) == {
        "title": "Children's Literature",
        "characters": 0,
    }


def test_code_text_empty():
    r64 = iscc.code_text(b"", text_granular=False)
    assert ContentCodeText(**r64)
    assert r64 == dict(iscc="EAASL4F2WZY7KBXB", characters=0)
    r128 = iscc.code_text(b"", text_bits=128, text_granular=False)
    assert r128 == dict(iscc="EABSL4F2WZY7KBXBYUZPREWZ26IXU", characters=0)

    with pytest.raises(AssertionError):
        iscc.metrics.distance(r64["iscc"], r128["iscc"])

    assert iscc.metrics.distance(Code(r64["iscc"]), Code(r128["iscc"]), mixed=True) == 0


def test_code_text_nogrn():
    a = iscc.code_text(TEXT_A.encode("utf-8"), text_granular=False)
    assert a == {
        "characters": 291,
        "iscc": "EAAR7BVKOFMBVNE4",
        "language": "en",
        "title": "Their most significant and usefull property of similaritypreserving",
    }
    b = iscc.code_text(TEXT_B.encode("utf-8"), text_granular=False)
    assert b == {
        "characters": 289,
        "iscc": "EAAR7BVKOFMBVNGM",
        "language": "en",
        "title": "The most significant and usefull property of similaritypreserving",
    }
    assert iscc.metrics.distance(a["iscc"], b["iscc"]) == 2


def test_code_text_granular():
    a = iscc.code_text(
        TEXT_A.encode("utf-8"), text_granular=True, text_avg_chunk_size=100
    )
    assert a == {
        "characters": 291,
        "iscc": "EAAR7BVKOFMBVNE4",
        "features": {
            "features": ["XYy_cVAdfP8", "7LaIeVSCsaA", "_pZVWTpBYOY", "kSem2vF2HOo"],
            "sizes": [78, 91, 66, 56],
            "kind": "text",
            "version": 0,
        },
        "language": "en",
        "title": "Their most significant and usefull property of similaritypreserving",
    }
    b = iscc.code_text(
        TEXT_B.encode("utf-8"), text_granular=True, text_avg_chunk_size=100
    )
    assert b == {
        "characters": 289,
        "iscc": "EAAR7BVKOFMBVNGM",
        "features": {
            "features": ["XY29cVA9fO4", "7LaIeVSCsaA", "_pZVWTpBYOY", "kSem2vF2HOo"],
            "sizes": [76, 91, 66, 56],
            "kind": "text",
            "version": 0,
        },
        "language": "en",
        "title": "The most significant and usefull property of similaritypreserving",
    }
    assert iscc.metrics.distance(a["iscc"], b["iscc"]) == 2


def test_hash_text():
    a = iscc.text.hash_text(TEXT_A).hex()
    b = iscc.text.hash_text(TEXT_B).hex()
    c = iscc.text.hash_text(TEXT_C).hex()
    assert a == "1f869a735c10bf9c32107ab4114e13d2bf93614cda99513ee9f989faf3d6983f"
    assert b == "1f869a735c18bfcc32107ab4114e13d2bf9b614cda91513ee9f189faf3d6987f"
    assert c == "366f2f1b08ba65efbbb48acf4b9953d144be674fa0af8802e7a6f1769b19c576"
    assert iscc.metrics.distance_hex(a, b) == 7


def test_extract_text_features_ta():
    result = iscc.text.extract_text_features(
        TEXT_A, text_avg_chunk_size=64, text_ngram_size=13
    )
    assert sum(result["sizes"]) == len(TEXT_A)
    assert result == {
        "features": [
            "HY83eFAhXsU",
            "tJCNM3GDmqo",
            "ybOgbVaQd6w",
            "757uWe5BwGY",
            "saWu27FmmP4",
            "fCr9n6iDBWo",
        ],
        "sizes": [88, 43, 52, 70, 41, 20],
        "kind": "text",
        "version": 0,
    }


def test_extract_text_features_tb():

    result = iscc.text.extract_text_features(
        TEXT_B, text_avg_chunk_size=64, text_ngram_size=13
    )
    assert sum(result["sizes"]) == len(TEXT_B)
    assert result == {
        "features": [
            "3uSY7q8UwUg",
            "nYc2flAhXsU",
            "tJCNM3GDmqo",
            "ybOgbVaQd6w",
            "757uWe5BwGY",
            "saWu27FmmP4",
            "fCr9n6iDBWo",
        ],
        "sizes": [20, 66, 43, 52, 70, 41, 20],
        "kind": "text",
        "version": 0,
    }


def test_chunk_text():
    txt = gen_utf8(1024 * 100)
    chunks = list(iscc.text.chunk_text(txt, text_avg_chunk_size=1024))
    assert "".join(chunks) == txt


def test_chunkt_text_options():
    txt = iscc.text.extract_text(texts()[0])
    ntxt = iscc.text.normalize_text(txt)
    assert len(ntxt) == 6048
    chunks = list(iscc.text.chunk_text(ntxt, text_avg_chunk_size=512))
    assert len(chunks) == 7


def test_trim_text():
    multibyte_2 = "ü" * 128
    trimmed = iscc.text.trim_text(multibyte_2, 128)
    assert 64 == len(trimmed)
    assert 128 == len(trimmed.encode("utf-8"))

    multibyte_3 = "驩" * 128
    trimmed = iscc.text.trim_text(multibyte_3, 128)
    assert 42 == len(trimmed)
    assert 126 == len(trimmed.encode("utf-8"))

    mixed = "Iñtërnâtiônàlizætiøn☃💩" * 6
    trimmed = iscc.text.trim_text(mixed, 128)
    assert 85 == len(trimmed)
    assert 128 == len(trimmed.encode("utf-8"))


def test_normalize_text():
    txt = "  Iñtërnâtiôn\nàlizætiøn☃💩 –  is a tric\t ky \u00A0 thing!\r"

    normalized = iscc.text.normalize_text(txt)
    assert normalized == "Internation alizætiøn☃💩 is a tric ky thing!"

    assert iscc.text.normalize_text(" ") == ""
    assert iscc.text.normalize_text("  Hello  World ? ") == "Hello World ?"
    assert iscc.text.normalize_text("Hello\nWorld") == "Hello World"
