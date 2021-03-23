# -*- coding: utf-8 -*-
import pytest
import iscc
import iscc_samples


@pytest.fixture
def idx():
    idx = iscc.Index("test-db")
    yield idx
    idx.destory()


@pytest.fixture
def full_iscc():
    return iscc.Code.rnd(mt=iscc.MT.ISCC, bits=256)


@pytest.fixture
def ten_isccs():
    return [iscc.Code.rnd(mt=iscc.MT.ISCC, bits=256) for _ in range(10)]


@pytest.fixture
def iscc_result():
    return iscc.code_iscc(iscc_samples.videos()[0], video_granular=True)


def test_index_name(idx):
    assert idx.name == "test-db"


def test_index_len(idx, full_iscc):
    assert len(idx) == 0
    idx.add(full_iscc.code)
    assert len(idx) == 1


def test_index_add_returns_id(idx, full_iscc):
    assert idx.add(full_iscc) == 0
    assert idx.add(iscc.Code.rnd(iscc.MT.ISCC, bits=256)) == 1


def test_index_add_no_dupes(idx, full_iscc):
    idx.add(full_iscc.code)
    assert len(idx) == 1
    idx.add(full_iscc.code)
    assert len(idx) == 1


def test_index_get_id(idx, ten_isccs):
    for code in ten_isccs:
        idx.add(code.code)
    assert idx.get_id(ten_isccs[0].code) == 0
    assert idx.get_id(ten_isccs[-1].code) == 9
    assert idx.get_id(iscc.Code.rnd(iscc.MT.ISCC, bits=256)) is None


def test_index_map_size(idx):
    assert idx.map_size == 2 ** 20


def test_index_in(idx, full_iscc):
    idx.add(full_iscc.code)
    assert full_iscc.code in idx
    # check random code not in index
    assert iscc.Code.rnd(mt=iscc.MT.ISCC, bits=256).code not in idx


def test_index_dbs_default(idx, iscc_result):
    # Default index
    assert idx.dbs() == []
    idx.add(iscc_result)
    assert idx.dbs() == [b"components", b"isccs"]


def test_index_dbs_features():
    # Index with freatures
    idx = iscc.Index("test-db-features", index_features=True)
    iscc_result = iscc.code_iscc(iscc_samples.videos()[0], video_granular=True)
    idx.add(iscc_result)
    try:
        assert idx.dbs() == [b"components", b"isccs", b"video"]
    finally:
        idx.destory()


def test_index_dbs_metadata():
    # Index with metadata
    idx = iscc.Index("test-db-metadata", index_metadata=True)
    iscc_result = iscc.code_iscc(iscc_samples.videos()[0], video_granular=True)
    idx.add(iscc_result)
    try:
        assert idx.dbs() == [b"components", b"isccs", b"metadata"]
    finally:
        idx.destory()


def test_index_iscc(idx, full_iscc):
    idx.add(full_iscc.code)
    assert idx.iscc(0) == full_iscc.bytes
    assert idx.iscc(1) is None


def test_index_isccs(idx):
    a = iscc.Code.rnd(mt=iscc.MT.ISCC, bits=256)
    b = iscc.Code.rnd(mt=iscc.MT.ISCC, bits=256)
    idx.add(a.code)
    idx.add(b.code)
    codes = [iscc.Code(c) for c in idx.isccs()]
    assert codes == [a, b]


def test_index_components(idx, full_iscc):
    idx.add(full_iscc.code)
    components_orig = set([c.bytes for c in iscc.decompose(full_iscc)])
    compenents_idx = set(idx.components())
    assert compenents_idx == components_orig
