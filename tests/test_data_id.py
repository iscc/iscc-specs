# -*- coding: utf-8 -*-
import random
import iscc
from tests.utils import static_bytes


def test_data_id_empty():
    assert iscc.data_id(b"") == "GAASL4F2WZY7KBXB"


def test_data_id_1byte():
    assert iscc.data_id(b"\x00") == "GAAXOD4P2IS6YHS2"


def test_data_id_1mib():
    data = bytearray(static_bytes(1024 * 1024))
    assert iscc.data_id(data) == "GAA6LM626EIYZ4E4"
    data.insert(500000, 1)
    assert iscc.data_id(data) == "GAA6LM626EIYZ4E4"
    data.insert(500001, 2)
    assert iscc.data_id(data) == "GAA6LM626EIYZ4E4"
    data.insert(500002, 3)
    assert iscc.data_id(data) == "GAA6LM626EIYZ4E4"


def test_data_id_changes():
    random.seed(1)
    data = bytearray([random.getrandbits(8) for _ in range(1000000)])  # 1 mb
    did_a = iscc.data_id(data)
    assert did_a == "GAA65ZWUJOQX2QVK"
    for x in range(10):  # insert 100 bytes random noise
        data.insert(random.randint(0, 1000000), random.randint(0, 255))
    did_b = iscc.data_id(data)
    assert did_b == "GAA65ZWUJOQXYAVK"
    assert iscc.distance(did_a, did_b) == 2
