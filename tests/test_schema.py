# -*- coding: utf-8 -*-
import iscc
import pytest
import os
from pydantic import ValidationError
from iscc import schema
from iscc_core import codec


def test_video_features_only():
    features = [codec.encode_base64(d) for d in [os.urandom(8) for _ in range(10)]]
    vf = schema.Features(features=features, version=0, kind=schema.FeatureType.video)
    assert vf.window == 7
    assert vf.overlap == 3
    assert vf.type_id == "video-0"


def test_video_features_checks_codes():
    features = []
    with pytest.raises(ValidationError):
        schema.Features(features=features, version=0, kind=schema.FeatureType.video)

    features = ["A"]
    with pytest.raises(ValidationError):
        schema.Features(features=features, version=0, kind=schema.FeatureType.video)

    features = ["AAAAAAAAAAA"]
    assert schema.Features(features=features, version=0, kind=schema.FeatureType.video)

    features = ["AAAAAAAAAA="]
    with pytest.raises(ValidationError):
        schema.Features(features=features, version=0, kind=schema.FeatureType.video)


def test_feature_match_distance():
    s = codec.encode_base64(b"\x00\x00\x00\x00\x00\x00\x00\x00")
    t = codec.encode_base64(b"\x00\x00\x00\x00\x00\x00\x00\x03")
    fm = schema.FeatureMatch(
        matched_iscc=codec.Code.rnd().code,
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
            schema.FeatureMatch(
                matched_iscc=codec.Code.rnd().code,
                kind="video",
                source_feature=codec.encode_base64(os.urandom(8)),
                matched_feature=codec.encode_base64(os.urandom(8)),
                matched_position=10,
            )
        )

    sorted_matches = sorted(matches)
    distances = [m.distance for m in sorted_matches]
    assert distances == sorted(distances)


def test_feature_int_float():
    feat = codec.encode_base64(os.urandom(8))
    ft = schema.Features(
        kind="text", version=0, features=[feat, feat, feat], sizes=[0, 1, 2]
    )
    assert isinstance(ft.sizes[0], int)
    ft = schema.Features(
        kind="text", version=0, features=[feat, feat, feat], sizes=[0.0, 1.1, 2.1]
    )
    assert isinstance(ft.sizes[0], float)
