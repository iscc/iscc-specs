# -*- coding: utf-8 -*-
import iscc
import pytest
import os
from pydantic import ValidationError
from iscc import schema
from iscc.codec import encode_base64
import iscc_samples


def test_video_features_only():
    features = [encode_base64(d) for d in [os.urandom(8) for _ in range(10)]]
    vf = schema.Features(features=features)
    assert vf.window == 7
    assert vf.overlap == 3


def test_video_features_checks_codes():
    features = []
    with pytest.raises(ValidationError):
        schema.Features(features=features)

    features = ["A"]
    with pytest.raises(ValidationError):
        schema.Features(features=features)

    features = ["AAAAAAAAAAA"]
    assert schema.Features(features=features)

    features = ["AAAAAAAAAA="]
    with pytest.raises(ValidationError):
        schema.Features(features=features)


def test_feature_match_distance():
    s = encode_base64(b"\x00\x00\x00\x00\x00\x00\x00\x00")
    t = encode_base64(b"\x00\x00\x00\x00\x00\x00\x00\x03")
    fm = schema.FeatureMatch(
        kind="text", source_hash=s, source_pos=0, target_hash=t, target_pos=0
    )
    assert fm.distance == 2
