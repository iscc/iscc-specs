# -*- coding: utf-8 -*-
import pytest
from iscc.core import content_id_video


def test_content_id_video():
    assert content_id_video([tuple(range(380))]) == "CTURv6NMw3oub"


def test_content_id_video_0_features():
    with pytest.raises(AssertionError):
        content_id_video([tuple([0] * 380)])
