# -*- coding: utf-8 -*-
from iscc.wtahash import wtahash, wta_permutations, WTA_SEED, WTA_VIDEO_ID_PERMUTATIONS


def test_permutations():
    assert wta_permutations(WTA_SEED, 380, 256) == WTA_VIDEO_ID_PERMUTATIONS


def test_wtahash_64():
    vec = tuple([0] * 379) + (1,)
    assert wtahash(vec, 64).hex() == "ffffffffffffffff"
    vec = (1,) + tuple([0] * 379)
    assert wtahash(vec, 64).hex() == "ffffffffffffffff"
    vec = (1,) + tuple([0] * 378) + (1,)
    assert wtahash(vec, 64).hex() == "ffffffffffffffff"
    vec = (0,) + tuple([2] * 378) + (0,)
    assert wtahash(vec, 64).hex() == "0000000000000000"
    vec = tuple(range(380))
    assert wtahash(vec, 64).hex() == "528f91431f7c4ad2"


def test_wtahash_256():
    vec = tuple([0] * 379) + (1,)
    assert (
        wtahash(vec, 256).hex()
        == "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )
    vec = (1,) + tuple([0] * 379)
    assert (
        wtahash(vec, 256).hex()
        == "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )
    vec = (1,) + tuple([0] * 378) + (1,)
    assert (
        wtahash(vec, 256).hex()
        == "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )
    vec = (0,) + tuple([2] * 378) + (0,)
    assert (
        wtahash(vec, 256).hex()
        == "0000000000000000000000000000000000000000000000000000000000000000"
    )
    vec = tuple(range(380))
    assert (
        wtahash(vec, 256).hex()
        == "528f91431f7c4ad26932fc073a28cac93f21a3071a152fc2925bdaed1d190061"
    )


def test_wtahash_prefix_stable():
    vec = tuple(reversed(range(380)))
    assert wtahash(vec, 256).hex()[:16] == wtahash(vec, 64).hex()
