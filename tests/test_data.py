import io
import random
import pytest
from iscc_core import code_data
from tests.utils import static_bytes


def test_hash_data_empty():
    assert (
        code_data.soft_hash_data_v0(io.BytesIO(b"")).hex()
        == "25f0bab671f506e1c532f892d9d7917a252e7a520832f5963a8cd4e9a7e312b5"
    )


def test_hash_data_zero():
    assert (
        code_data.soft_hash_data_v0(io.BytesIO(b"\x00")).hex()
        == "770f8fd225ec1e5abb95e406afaddef303defe2f0d03b74c388f7b42ef96c7af"
    )


def test_hash_data_bad_types():
    with pytest.raises(AttributeError):
        code_data.soft_hash_data_v0(None)

    with pytest.raises(AttributeError):
        code_data.soft_hash_data_v0(0)


def test_hash_data_1mib_robust():
    random.seed(1)
    mib = 1024 * 1024
    ba = bytearray(static_bytes(mib))
    rbyte = lambda: random.randint(0, 256)
    rpos = lambda: random.randint(0, mib)

    # 9 random single byte changes in data
    h1 = code_data.soft_hash_data_v0(io.BytesIO(ba)).hex()
    assert h1 == "e5b3daf1118cf09cb5c5ac323a9f68ca04465f9e3942297ebd1e6360f5bb98df"
    for x in range(9):
        ba.insert(rpos(), rbyte())
        assert code_data.soft_hash_data_v0(io.BytesIO(ba)).hex() == h1

    # 1-bit difference on 10th byte change
    ba.insert(rpos(), rbyte())
    h2 = code_data.soft_hash_data_v0(io.BytesIO(ba)).hex()
    assert h1 != h2
