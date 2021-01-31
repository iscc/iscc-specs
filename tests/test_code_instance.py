# -*- coding: utf-8 -*-
import iscc


def test_code_instance_empty():
    result = iscc.code_instance(b"")
    assert result == {
        "code": "IAA26E2JXH27TING",
        "datahash": "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262",
        "filesize": 0,
    }


def test_code_instance_zero():
    result = iscc.code_instance(b"\00")
    assert result == {
        "code": "IAAS2OW637YRWYPR",
        "datahash": "2d3adedff11b61f14c886e35afa036736dcd87a74d27b5c1510225d0f592e213",
        "filesize": 1,
    }


def test_code_instance_even():
    zero_bytes_even = b"\x00" * 16
    result = iscc.code_instance(zero_bytes_even)
    assert result == {
        "code": "IAA6K4W77ARQI4AL",
        "datahash": "e572dff82304700b856a555ac3a4558d0df3646a3727816500270a93c66aac1e",
        "filesize": 16,
    }


def test_code_instance_uneven():
    ff_bytes_uneven = b"\xff" * 17
    result = iscc.code_instance(ff_bytes_uneven)
    assert result == {
        "code": "IAA37KWEEXC5NXLC",
        "datahash": "bfaac425c5d6dd620fb602a27ddea841cf426184094497f59d881be9d8b1601c",
        "filesize": 17,
    }


def test_code_instance_more_bytes():
    more_bytes = b"\xcc" * 66000
    result = iscc.code_instance(more_bytes)
    assert result == {
        "code": "IAAT4ST2A3XFM7AQ",
        "datahash": "3e4a7a06ee567c101c67de35d12bea6c5e70b424ede1502d54a848f9319a4c27",
        "filesize": 66000,
    }


def test_code_instance_256():
    data = b"\xcc" * 66000
    result = iscc.code_instance(data, instance_bits=256)
    assert result == {
        "code": "IADT4ST2A3XFM7AQDRT54NORFPVGYXTQWQSO3YKQFVKKQSHZGGNEYJY",
        "datahash": "3e4a7a06ee567c101c67de35d12bea6c5e70b424ede1502d54a848f9319a4c27",
        "filesize": 66000,
    }
