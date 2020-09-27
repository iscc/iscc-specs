# -*- coding: utf-8 -*-
import pytest
import iscc


def test_minhash_empty():
    with pytest.raises(ValueError):
        iscc.minhash([])


def test_minhash_single_feature():
    mh = iscc.minhash([2 ** 16])
    assert isinstance(mh, list)
    assert len(mh) == 64
    assert mh[0] == 1968499307
    assert mh[-1] == 2739100501


def test_minhash_32bit_features():
    i32 = 2 ** 32 - 1
    mh = iscc.minhash([2 ** 64 - 1])
    for n in mh:
        assert n <= i32


def test_minhash_compress():
    mh = iscc.minhash([2 ** 16])
    digest = iscc.compress(mh)
    assert len(digest) == 32
    assert (
        digest.hex()
        == "a18e2fb2bd663d21db9c7dcc9ae78380253cae5bf089766d87a6b51fcb3f8f8e"
    )
    mh = [0b0001, 0b0010, 0b0100, 0b1000]
    compressed = iscc.compress(mh)
    as_int = int.from_bytes(compressed, "big", signed=False)
    assert as_int == 0b1000_0100_0010_0001
