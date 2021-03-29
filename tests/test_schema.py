# -*- coding: utf-8 -*-
import iscc
import pytest
import os
from pydantic import ValidationError
from iscc import schema
from iscc.codec import encode_base64


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
        matched_iscc=iscc.Code.rnd().code,
        kind="text",
        source_feature=s,
        source_pos=0,
        matched_feature=t,
        matched_position=0,
    )
    assert fm.distance == 2


def test_query_result():
    qr = schema.QueryResult()
    assert qr.iscc_matches == []
    assert qr.feature_matches == []


def test_feature_match_sortable():
    matches = []
    for x in range(10):
        matches.append(
            iscc.FeatureMatch(
                matched_iscc=iscc.Code.rnd().code,
                kind="video",
                source_feature=iscc.encode_base64(os.urandom(8)),
                matched_feature=iscc.encode_base64(os.urandom(8)),
                matched_position=10,
            )
        )

    sorted_matches = sorted(matches)
    distances = [m.distance for m in sorted_matches]
    assert distances == sorted(distances)
