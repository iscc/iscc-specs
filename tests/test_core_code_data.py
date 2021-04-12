# -*- coding: utf-8 -*-
import random
from statistics import mean

import iscc
from tests.test_readables import text_readables
from tests.utils import static_bytes


def test_code_data_empty():
    assert iscc.code_data(b"") == {"code": "GAASL4F2WZY7KBXB"}


def test_code_data_1byte():
    assert iscc.code_data(b"\x00") == {"code": "GAAXOD4P2IS6YHS2"}


def test_code_data_1mib_robustness():

    random.seed(1)
    mib = 1024 * 1024
    data = bytearray(static_bytes(mib))
    rbyte = lambda: random.randint(0, 256)
    rpos = lambda: random.randint(0, mib)

    # random single byte changes in data
    c1 = iscc.code_data(data)
    assert c1 == {"code": "GAA6LM626EIYZ4E4"}
    for x in range(9):
        data.insert(rpos(), rbyte())
        assert iscc.code_data(data) == c1

    # 1-bit difference on 10th byte change
    data.insert(rpos(), rbyte())
    c2 = iscc.code_data(data)
    assert iscc.distance(c1["code"], c2["code"]) == 1


def test_code_data_extends():
    data = bytearray(static_bytes(1024 * 64))
    assert iscc.code_data(data) == {"code": "GAA74QF35A7CJLWA"}
    assert iscc.code_data(data, data_bits=256) == {
        "code": "GAD74QF35A7CJLWAU6XWQYN4K2YMV7KGDXMVXMYHOJFKRGJ7HUFLFUY"
    }


def test_code_data_random_changes():
    random.seed(1)
    data = bytearray([random.getrandbits(8) for _ in range(1000000)])  # 1 mb
    did_a = iscc.code_data(data)
    assert did_a == {"code": "GAA65ZWUJOQX2QVK"}
    for x in range(10):  # insert 10 bytes random noise
        data.insert(random.randint(0, 1000000), random.randint(0, 255))
    did_b = iscc.code_data(data)
    assert did_b == {"code": "GAA65ZWUJOQXYAVK"}
    assert iscc.distance(did_a["code"], did_b["code"]) == 2


def test_code_data_inputs():
    for rb in text_readables():
        result = iscc.code_data(rb)
        assert result == {"code": "GAAYGICYTOZYKQAL"}


def test_code_data_granular():
    data = bytearray(static_bytes(1024 * 1024))
    a = iscc.code_data(
        data, data_granular=True, data_avg_chunk_size=1024, data_granular_factor=64
    )
    assert a == {
        "code": "GAA6LM626EIYZ4E4",
        "features": {
            "features": [
                "_kS7wD4kvsA",
                "_3GTQp7AlgQ",
                "-TjPB2hxj00",
                "ZQ7hpcaKqA0",
                "nnn0C0IL28U",
                "OCAg9xyUc00",
                "zB5L4U7zNI0",
                "_mMAKFQMTwQ",
                "TBV2kckb4Fw",
                "odjLbH8MaKw",
                "8Opao8TnUz0",
                "t-i8q4sN6D0",
                "tvM5jXLG8J4",
                "xtv501iHqxs",
                "67pRxkkBFrE",
                "-PwAa5vR6J8",
            ],
            "sizes": [
                71849,
                62221,
                69584,
                69566,
                63983,
                61275,
                65034,
                67510,
                64578,
                67387,
                66604,
                61790,
                70521,
                64208,
                61343,
                61123,
            ],
            "kind": "data",
            "version": 0,
        },
    }


def test_code_data_granular_1mib():
    data = bytearray(static_bytes(1024 * 1024))
    a = iscc.code_data(data, data_granular=False, data_avg_chunk_size=1024)
    b = iscc.code_data(
        data, data_granular=True, data_avg_chunk_size=1024, data_granular_factor=64
    )
    assert a == {"code": "GAA6LM626EIYZ4E4"}
    assert a["code"] == b["code"]
    assert sum(b["features"]["sizes"]) == len(data)
    assert b["features"]["sizes"] == [
        71849,
        62221,
        69584,
        69566,
        63983,
        61275,
        65034,
        67510,
        64578,
        67387,
        66604,
        61790,
        70521,
        64208,
        61343,
        61123,
    ]
    assert b["features"]["features"] == [
        "_kS7wD4kvsA",
        "_3GTQp7AlgQ",
        "-TjPB2hxj00",
        "ZQ7hpcaKqA0",
        "nnn0C0IL28U",
        "OCAg9xyUc00",
        "zB5L4U7zNI0",
        "_mMAKFQMTwQ",
        "TBV2kckb4Fw",
        "odjLbH8MaKw",
        "8Opao8TnUz0",
        "t-i8q4sN6D0",
        "tvM5jXLG8J4",
        "xtv501iHqxs",
        "67pRxkkBFrE",
        "-PwAa5vR6J8",
    ]


def test_code_data_granular_robust():
    random.seed(1)
    data = bytearray([random.getrandbits(8) for _ in range(1000000)])  # 1 mb
    code_a = iscc.code_data(data, data_granular=True)
    assert code_a["code"] == "GAA65ZWUJOQX2QVK"
    for x in range(100):  # insert 100 bytes random noise
        data.insert(random.randint(0, 1000000), random.randint(0, 255))
    code_b = iscc.code_data(data, data_granular=True)
    assert code_b["code"] == "GAA65ZWUJOQXYBVK"
    assert iscc.distance(code_a["code"], code_b["code"]) == 3
    assert len(code_a["features"]["features"]) == len(code_b["features"]["features"])

    # Pairwise granular hashes should have low average distance
    distances = []
    for gfa, gfb in zip(code_a["features"]["features"], code_b["features"]["features"]):
        dist = iscc.distance_b64(gfa, gfb)
        assert dist < 15
        distances.append(dist)
    assert mean(distances) < 7
