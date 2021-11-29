# -*- coding: utf-8 -*-
import iscc_core


def test_meta_empty():
    m = iscc_core.soft_hash_meta_v0("")
    assert len(m) == 32
    assert m.hex() == "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"


def test_meta_extra_only():
    m = iscc_core.soft_hash_meta_v0("", "Hello")
    assert len(m) == 32
    assert m.hex() == "af1349b9652ce5bbf5f9a1a63fd7018aa0404dea8746265c36dcc949d8a542f4"


def test_meta_interleaved():
    ma = iscc_core.soft_hash_meta_v0("", "")
    mb = iscc_core.soft_hash_meta_v0("", "hello")
    assert ma[:4] == mb[:4]
    assert ma[4:8] == mb[8:12]
