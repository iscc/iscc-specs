# -*- coding: utf-8 -*-
from .utils import static_bytes
from iscc import merkle


def test_tophash_zero_byte():
    th = merkle.tophash(b"\x00")
    assert th == "1ad48f49627079d806b802c74f40c39d55fe1d78b3faf0f8017aec62cec42122"


def test_tophash_8_bytes():
    th = merkle.tophash(static_bytes(8))
    assert th == "1029321c215f1d4dbdcc12c8a607155c9f87a6eafd0d4efb16746ba48041b954"


def test_tophash_even_leaves():
    th = merkle.tophash(static_bytes(merkle.LEAF_SIZE + 1))
    assert th == "f328057c2d072358ac2a3bd9a82480e3721fbbcfbb049e95506c75313fabc2cb"


def test_tophash_odd_leaves():
    th = merkle.tophash(static_bytes(merkle.LEAF_SIZE * 2 + 1))
    assert th == "d8a827dcf3b0e46dc126cbcde576359b84ba647cc6df958101ee0ae48856e32a"
