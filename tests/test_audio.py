# -*- coding: utf-8 -*-
from iscc.core import content_id_audio


def test_content_id_audio_empty():
    assert content_id_audio([]) == "CFSVvzFyWvGoT"


def test_content_id_audio_single():
    assert content_id_audio([1]) == "CFSVvzG63w6wD"


def test_content_id_audio_short():
    assert content_id_audio([1, 2]) == "CFSVvzG63w6wb"


def test_content_id_audio_signed():
    assert content_id_audio([-1, 0, 1]) == "CGW1wBpWb979M"
