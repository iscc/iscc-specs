# -*- coding: utf-8 -*-
import pytest
from iscc import metrics
from bitarray.util import int2ba
from iscc.core import code_meta
from iscc.codec import Code

A_INT = 0b0000_0000_0000_1111
B_INT = 0b1111_0000_0000_1111
C_INT = 0b0000_1111
A_BYT = A_INT.to_bytes(length=2, byteorder="big", signed=False)
B_BYT = B_INT.to_bytes(length=2, byteorder="big", signed=False)
C_BYT = C_INT.to_bytes(length=2, byteorder="big", signed=False)
A_CODE = Code(code_meta("Hello World Hello World Hello World Hello World")["code"])
B_CODE = Code(code_meta("Hello World Hello World Hello World Hello Worlt")["code"])
C_CODE = Code(
    code_meta("Hello World Hello World Hello World Hello Worlt", meta_bits=256)["code"]
)


def test_distance():
    assert metrics.distance(A_CODE, B_CODE) == 4
    assert metrics.distance(A_CODE.code, B_CODE.code) == 4
    assert metrics.distance(A_CODE.hash_bytes, B_CODE.hash_bytes) == 4
    assert metrics.distance(A_CODE.hash_uint, B_CODE.hash_uint) == 4


def test_distance_mixed():
    assert metrics.distance(A_CODE, C_CODE, mixed=True) == 4
    assert metrics.distance(A_CODE.code, C_CODE.code, mixed=True) == 4
    assert metrics.distance(A_CODE.hash_bytes, C_CODE.hash_bytes, mixed=True) == 4
    assert metrics.distance(A_INT, C_INT, mixed=True) == 0


def test_distance_strict():
    with pytest.raises(AssertionError):
        assert metrics.distance(A_CODE, C_CODE)
    with pytest.raises(AssertionError):
        assert metrics.distance(A_CODE.code, C_CODE.code)
    with pytest.raises(ValueError):
        assert metrics.distance(A_CODE.hash_bytes, C_CODE.hash_bytes)
    assert metrics.distance(A_CODE.hash_uint, C_CODE.hash_uint)


def test_distance_code_strict():
    assert metrics.distance_code(A_CODE.code, B_CODE.code) == 4
    with pytest.raises(AssertionError):
        assert metrics.distance_code(A_CODE.code, C_CODE.code)


def test_distance_code_mixed():
    assert metrics.distance_code(A_CODE.code, B_CODE.code, mixed=True) == 4
    assert metrics.distance_code(A_CODE.code, C_CODE.code, mixed=True) == 4


def test_dinstance_int():
    assert metrics.distance_int(A_INT, B_INT) == 4
    assert metrics.distance_int(A_INT, C_INT) == 0


def test_distance_bytes():
    assert metrics.distance_bytes(A_CODE.hash_bytes, B_CODE.hash_bytes) == 4
    with pytest.raises(ValueError):
        assert metrics.distance_bytes(A_CODE.hash_bytes, C_CODE.hash_bytes)


def test_distance_hex():
    assert metrics.distance_hex(A_BYT.hex(), B_BYT.hex()) == 4
    assert metrics.distance_hex(A_BYT.hex(), C_BYT.hex()) == 0
    with pytest.raises(ValueError):
        metrics.distance_hex(A_CODE.hash_hex, C_CODE.hash_hex)


def test_distance_ba():
    A_BA = int2ba(A_INT, length=16)
    B_BA = int2ba(B_INT, length=16)
    C_BA = int2ba(C_INT, length=8)
    assert metrics.distance_ba(A_BA, B_BA) == 4
    with pytest.raises(ValueError):
        assert metrics.distance_ba(A_BA, C_BA)


def test_compare():
    a = "KADTF57DEXU74AIAAA76KJQ5AQTHALDO5JXPCRCRC422GN2RKUYCZ3A"
    b = "KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3PE2RQEAMBDN4MA"
    assert metrics.compare(a, b) == {"ddist": 30, "imatch": False, "mdist": 30}
    c = "KMD73CA6R4XJLI5CKYOYF7CYSL5PSBWQO33FNHPQNNCY4KHZALJ54JA"
    assert metrics.compare(b, c) == {
        "cdist": 4,
        "ddist": 32,
        "imatch": False,
        "mdist": 28,
    }
