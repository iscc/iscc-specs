# -*- coding: utf-8 -*-
from iscc.core import content_id_audio


def test_content_id_audio_empty():
    assert content_id_audio([]) == "EIAQAAAAAAAAAAAA"


def test_content_id_audio_single():
    assert content_id_audio([1]) == "EIAQAAAAAEAAAAAA"


def test_content_id_audio_short():
    assert content_id_audio([1, 2]) == "EIAQAAAAAEAAAAAC"


def test_content_id_audio_signed():
    assert content_id_audio([-1, 0, 1]) == "EIA7777774AAAAAA"


def test_content_id_audio_128_bit():
    assert content_id_audio([-1, 0, 1], 128) == "EIB7777774AAAAAAAAAAAAIAAAAAA"
