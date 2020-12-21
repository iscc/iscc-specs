# -*- coding: utf-8 -*-
import pytest
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


def test_needs_two_uniques():
    with pytest.raises(AssertionError):
        wtahash([1, 1])


def test_any_vector_length():
    assert wtahash([1, 2], 64).hex() == "a4a91662a8728c07"
    assert wtahash([1, 2], 128).hex() == "a4a91662a8728c07660bad1ceb784b2a"
    assert wtahash(range(1024), 64).hex() == "a2582f1885555623"
    assert (
        wtahash(range(1024), 196).hex()
        == "a2582f18855556238d26ba4b8c2c023687c3e81dc83c6128d0"
    )
