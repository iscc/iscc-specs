# -*- coding: utf-8 -*-
from iscc import code_iscc_id
from iscc_core.codec import Code

CODE = Code("KEDRJQYSNTXPLI6Q4J7FBWCM2PTEKCYQSOFOE3SCWPWEG3DJSCJUDCI")
CODE_UNC = "AAARJQYSNTXPLI6Q-EEA6E7SQ3BGNHZSF-GAAQWEETRLRG4QVT-IAA6YQ3MNGIJGQMJ"
EXPECT = {"iscc": "MAACAASSCLEO557C"}


def test_code_iscc_id_iscc_str():
    assert code_iscc_id(0, CODE.code, uc=0) == EXPECT


def test_code_iscc_id_iscc_str_unc():
    assert code_iscc_id(0, CODE_UNC, uc=0) == EXPECT


def test_code_iscc_id_iscc_obj():
    assert code_iscc_id(0, CODE, uc=0) == EXPECT


def test_code_iscc_id_iscc_bytes():
    assert code_iscc_id(0, CODE.bytes, uc=0) == EXPECT


def test_code_iscc_id_iscc_struct():
    assert code_iscc_id(0, CODE._head + (CODE.hash_bytes,), uc=0) == EXPECT
