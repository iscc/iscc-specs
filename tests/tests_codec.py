# -*- coding: utf-8 -*-
import pytest
from iscc.codec import *


def test_iscc_header_meta_code():
    header = ISCCHeader(MT_MC, ST_NONE)
    assert header.length == 64
    assert header.version == 0
    assert header.humanized == "meta-code.none.v0.64bits"


def test_iscc_header_content_code():
    header = ISCCHeader(MT_CC, ST_GMT_TXT)
    assert header.length == 64
    assert header.version == 0
    assert header.humanized == "content-code.text.v0.64bits"


def test_iscc_header_version():
    header = ISCCHeader(MT_MC, ST_NONE, 1)
    assert header.version == 1
    assert header.humanized == "meta-code.none.v1.64bits"


def test_iscc_header_length():
    header = ISCCHeader(MT_MC, ST_NONE, length=256)
    assert header.length == 256
    assert header.humanized.endswith("256bits")


def test_iscc_header_raises():
    with pytest.raises(AssertionError):
        ISCCHeader(8, 8)


def test_encode_base32():
    assert encode_base32(b"") == ""
    assert encode_base32(b"f") == "MY"
    assert encode_base32(b"fo") == "MZXQ"
    assert encode_base32(b"foo") == "MZXW6"
    assert encode_base32(b"foob") == "MZXW6YQ"
    assert encode_base32(b"fooba") == "MZXW6YTB"
    assert encode_base32(b"foobar") == "MZXW6YTBOI"
