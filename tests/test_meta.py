# -*- coding: utf-8 -*-
from iscc import meta


def test_meta_empty():
    m = meta.meta_hash("")
    assert len(m) == 32
    assert m.hex() == "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"


def test_meta_extra_only():
    m = meta.meta_hash("", "Hello")
    assert len(m) == 32
    assert m.hex() == "af1349b9652ce5bbf5f9a1a63fd7018aa0404dea8746265c36dcc949d8a542f4"


def test_meta_interleaved():
    ma = meta.meta_hash("", "")
    mb = meta.meta_hash("", "hello")
    assert ma[:4] == mb[:4]
    assert ma[4:8] == mb[8:12]
