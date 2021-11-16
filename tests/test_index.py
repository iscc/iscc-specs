# -*- coding: utf-8 -*-
import os
import msgpack
import pytest
import iscc
import iscc_samples
from iscc.schema import IsccMatch, FeatureMatch, QueryResult
import uuid


TEST_CODES = [
    "KADTF57DEXU74AIAAA76KJQ5AQTHALDO5JXPCRCRC422GN2RKUYCZ3A",
    "KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3PE2RQEAMBDN4MA",
    "KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3NPWULHXP5BXSJI",
    "KMD6P2X7C73P72Z4KYOYF7CYTL5PS5LXYSDEZPZMX65SY36REOETL6Q",
    "KMD73CA6R4XJLI5CKYOYF7CYSL5PSBWQO33FNHPQNNCY4KHZALJ54JA",
    "KMD6P2X7C73P72Z4KYOYF7CYSL5PTEZDYWYEPFJMWAWTF7WHOUTKTJI",
    "KID6P2X7C73P72Z4QA6KKL4AHSSS6PIUKCFGDEBNBO7U5R4OANSFPAQ",
    "KMD6P2X7C73P72Z4K2PIHNCYLLZPSPNWOCVGDFJNCNDFLFA4BBFYOVY",
    "KMD6P2X7C73P72Z4KYOYF7CYSL5PTRJEQGQ3C2MDKRES4YQH223CMQA",
    "KMD6P2X7C73P72Z4KYOYF7CYSL5PSBV2FQQ6IPDDX566E4CQO55IENY",
    "KMD73CA6R4XJLI5CKYOYF7CYSL5PS7G6RNNCWVCAXZFOBG5J3UAB4EA",
    "KMD73CA6R4XJLI5CKYOYF7CYTL5PSDTGHO52LVRXAELT2LOWOCGSFEQ",
    "KMD73CA6R4XJLI5CKYOYF7CYSL5PTKDOPDEUETYGNGGUADC5E5GWOBA",
]

QUERY_CODE = "KMD73CA6R4XJLI5CKYOYF7CYSL5PSJGVYXJVMT4PF3CSTGC4KNJ4ILI"


@pytest.fixture
def idx():
    idx = iscc.Index("test-db")
    yield idx
    idx.destroy()


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


def test_index_get_key(idx, full_iscc):
    assert len(idx) == 0
    key = idx.add(full_iscc)
    assert idx.get_key(full_iscc) == 0 == key
    i2 = iscc.Code.rnd(mt=iscc.MT.ISCC, bits=256)
    key = idx.get_key(i2)
    assert idx.get_key(i2) == 1 == key

# Todo: pass db.get_key after reopen
# def test_index_get_key_after_reopen(idx, full_iscc):
#     assert len(idx) == 0
#     key = idx.add(full_iscc)
#     assert idx.get_key(full_iscc) == 0 == key
#     idx.close()
#     idx = iscc.Index("test-db")
#     assert idx.get_key(full_iscc) == 0 == key


def test_index_len_autoid(idx, full_iscc):
    assert len(idx) == 0
    idx.add(full_iscc)
    assert len(idx) == 1


def test_index_contains(idx, full_iscc):
    idx.add(full_iscc)
    assert full_iscc.code in idx


def test_index_stats(idx, full_iscc):
    idx.add(full_iscc)
    assert idx.stats == {
        "comp-CONTENT-TEXT-V0-64": 1,
        "comp-DATA-NONE-V0-64": 1,
        "comp-INSTANCE-NONE-V0-64": 1,
        "comp-META-NONE-V0-64": 1,
        "isccs": 1,
    }


def test_index_key_int(idx, full_iscc):
    assert len(idx) == 0
    idx.add(full_iscc.code, 666)
    assert len(idx) == 1
    assert idx.get_iscc(666) == full_iscc


def test_index_key_str(idx, full_iscc):
    assert len(idx) == 0
    idx.add(full_iscc.code, "some-key")
    assert len(idx) == 1
    assert idx.get_iscc("some-key") == full_iscc


def test_index_add_returns_key(idx, full_iscc):
    assert idx.add(full_iscc) == 0
    assert idx.add(iscc.Code.rnd(iscc.MT.ISCC, bits=256)) == 1


def test_index_add_no_dupes(idx, full_iscc):
    idx.add(full_iscc.code)
    assert len(idx) == 1
    idx.add(full_iscc.code)
    assert len(idx) == 1


def test_index_get_key(idx, ten_isccs):
    for code in ten_isccs:
        idx.add(code.code)
    assert idx.get_key(ten_isccs[0].code) == 0
    assert idx.get_key(ten_isccs[-1].code) == 9
    assert idx.get_key(iscc.Code.rnd(iscc.MT.ISCC, bits=256)) is None


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
    assert idx.dbs() == [
        b"comp-CONTENT-VIDEO-V0-64",
        b"comp-DATA-NONE-V0-64",
        b"comp-INSTANCE-NONE-V0-64",
        b"comp-META-NONE-V0-64",
        b"isccs",
    ]


def test_index_dbs_features():
    # Index with freatures
    idx = iscc.Index("test-db-features", index_features=True)
    iscc_result = iscc.code_iscc(iscc_samples.videos()[0], video_granular=True)
    idx.add(iscc_result)
    try:
        assert idx.dbs() == [
            b"comp-CONTENT-VIDEO-V0-64",
            b"comp-DATA-NONE-V0-64",
            b"comp-INSTANCE-NONE-V0-64",
            b"comp-META-NONE-V0-64",
            b"feat-video-0",
            b"isccs",
        ]
    finally:
        idx.destroy()


def test_index_dbs_metadata():
    # Index with metadata
    idx = iscc.Index("test-db-metadata", index_metadata=True)
    iscc_result = iscc.code_iscc(iscc_samples.videos()[0], video_granular=True)
    idx.add(iscc_result)
    try:
        assert idx.dbs() == [
            b"comp-CONTENT-VIDEO-V0-64",
            b"comp-DATA-NONE-V0-64",
            b"comp-INSTANCE-NONE-V0-64",
            b"comp-META-NONE-V0-64",
            b"isccs",
            b"metadata",
        ]
    finally:
        idx.destroy()


def test_index_iscc(idx, full_iscc):
    idx.add(full_iscc.code)
    assert idx.get_iscc(0) == full_iscc
    assert idx.get_iscc(1) is None


def test_index_isccs(idx):
    a = iscc.Code.rnd(mt=iscc.MT.ISCC, bits=256)
    b = iscc.Code.rnd(mt=iscc.MT.ISCC, bits=256)
    idx.add(a.code)
    idx.add(b.code)
    codes = [iscc.Code(c) for c in idx.iter_isccs()]
    assert codes == [a, b]


def test_index_components(idx, full_iscc):
    idx.add(full_iscc.code)
    components_orig = set([c.hash_bytes for c in iscc.decompose(full_iscc)])
    compenents_idx = set(idx.iter_components())
    assert compenents_idx == components_orig


def test_add_component(idx):
    comp, fkey = iscc.Code.rnd(bits=64), os.urandom(8)
    idx._add_component(comp, fkey)
    db = idx._db_components(comp.type_id)
    assert idx._get_values(db, comp.hash_bytes) == [fkey]

    # is idempotent?
    idx._add_component(comp, fkey)
    assert idx._get_values(db, comp.hash_bytes) == [fkey]

    # dupe component with different fkey gets appended
    fkey2 = os.urandom(8)
    idx._add_component(comp, fkey2)
    assert set(idx._get_values(db, comp.hash_bytes)) == {fkey, fkey2}

    # dupe fkey for same component is ignored
    idx._add_component(comp, fkey)
    assert set(idx._get_values(db, comp.hash_bytes)) == {fkey, fkey2}


def test_add_feature(idx):
    kind, feature, fkey, pos = "video", os.urandom(8), os.urandom(6), 666
    idx._add_feature(kind, feature, fkey, pos)
    assert idx._get_feature(kind, feature) == [(fkey, pos)]

    # id idempotent?
    idx._add_feature(kind, feature, fkey, pos)
    assert idx._get_feature(kind, feature) == [(fkey, pos)]

    # same key with different position
    idx._add_feature(kind, feature, fkey, pos + 1)
    assert set(idx._get_feature(kind, feature)) == {(fkey, pos), (fkey, pos + 1)}

    # different key with same position
    fkey2 = os.urandom(8)
    idx._add_feature(kind, feature, fkey2, pos)
    assert set(idx._get_feature(kind, feature)) == {
        (fkey, pos),
        (fkey, pos + 1),
        (fkey2, pos),
    }


def test_query():
    idx = iscc.Index(
        "test-db",
    )
    for code in TEST_CODES:
        idx.add(code)
    idx.add(QUERY_CODE)
    assert idx.query(QUERY_CODE, k=3) == QueryResult(
        iscc_matches=[
            IsccMatch(
                key=13,
                matched_iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PSJGVYXJVMT4PF3CSTGC4KNJ4ILI",
                distance=0,
                mdist=0,
                cdist=0,
                ddist=0,
                imatch=True,
            ),
            IsccMatch(
                key=4,
                matched_iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PSBWQO33FNHPQNNCY4KHZALJ54JA",
                distance=48,
                mdist=0,
                cdist=0,
                ddist=26,
                imatch=False,
            ),
            IsccMatch(
                key=12,
                matched_iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PTKDOPDEUETYGNGGUADC5E5GWOBA",
                distance=52,
                mdist=0,
                cdist=0,
                ddist=27,
                imatch=False,
            ),
        ],
        feature_matches=[],
    )
    idx.destroy()


def test_index_match_component_exact():
    idx = iscc.Index("test-match-component", index_components=True)
    for i in TEST_CODES:
        idx.add(i)
    components = iscc.decompose(TEST_CODES[-1])
    fkeys = [msgpack.loads(fk) for fk in idx.match_component(components[0])]
    assert fkeys == [4, 10, 11, 12]
    idx.destroy()


def test_index_match_feature_exact():
    idx = iscc.Index("test-match-feature", index_features=True)
    feature = os.urandom(8)
    for i in TEST_CODES:
        idx.add(i)
    idx._add_feature("video", feature, msgpack.dumps(0), 100)
    r = idx.match_feature("video", feature, ft=0)
    assert len(r) == 1
    assert r[0].matched_iscc == TEST_CODES[0]
    idx.destroy()


def test_index_match_feature_similar():
    idx = iscc.Index("test-match-feature", index_features=True)
    feata = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    featb = b"\x00\x00\x00\x00\x00\x00\x00\x03"
    assert iscc.distance_bytes(feata, featb) == 2
    for i in TEST_CODES:
        idx.add(i)
    idx._add_feature("video", feata, msgpack.dumps(0), 100)
    r = idx.match_feature("video", featb, ft=2)
    assert len(r) == 1
    assert r[0].matched_iscc == TEST_CODES[0]
    idx.destroy()


def test_index_query_features():
    idx = iscc.Index("test-query-features", index_components=True, index_features=True)
    v0 = iscc.code_iscc(iscc_samples.videos()[0], video_granular=True)
    v1 = iscc.code_iscc(iscc_samples.videos()[1], video_granular=True)
    v2 = iscc.code_iscc(iscc_samples.videos()[2], video_granular=True)
    v3 = iscc.code_iscc(iscc_samples.videos()[3], video_granular=True)
    idx.add(v0)
    idx.add(v1)
    idx.add(v2)
    r = idx.query(v3, k=3, ct=1, ft=5)
    assert r == QueryResult(
        iscc_matches=[
            IsccMatch(
                key=2,
                matched_iscc="KMD73CA6R4XJLI5CKYOYF7CYTL5PSDTGHO52LVRXEGNXO4RA672UNMQ",
                distance=66,
                mdist=0,
                cdist=1,
                ddist=33,
                imatch=False,
            )
        ],
        feature_matches=[
            FeatureMatch(
                key=1,
                matched_iscc="KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3NPWULHXP5BXSJI",
                kind="video-0",
                source_feature="Vh2C_FiS-vk",
                source_pos=0,
                matched_feature="VpmC_FiSutk",
                matched_position=0,
                distance=4,
            ),
            FeatureMatch(
                key=0,
                matched_iscc="KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3PE2RQEAMBDN4MA",
                kind="video-0",
                source_feature="Vh2C_FiS-vk",
                source_pos=0,
                matched_feature="VpmC_FiSutk",
                matched_position=0,
                distance=4,
            ),
        ],
    )
    idx.destroy()


def test_index_audio_features():
    idx = iscc.Index(
        "test-index-audio-features", index_components=True, index_features=True
    )
    v0 = iscc.code_iscc(iscc_samples.audios()[0], audio_granular=True)
    v1 = iscc.code_iscc(iscc_samples.audios()[1], audio_granular=True)
    # change code so we can match by feature
    code = iscc.Code(v0["iscc"])
    nc = iscc.Code(code.header_bytes + (b"\xff" * 32))
    v0["iscc"] = nc.code
    idx.add(v0)

    assert idx.query(v1, k=10, ct=0, ft=5) == QueryResult(
        iscc_matches=[],
        feature_matches=[
            FeatureMatch(
                key=0,
                matched_iscc="KID777777777777777777777777777777777777777777777777777Y",
                kind="audio-0",
                source_feature="KMUSJSjEMjc",
                source_pos=0,
                matched_feature="KMUSJSjEMjc",
                matched_position=0,
                distance=0,
            )
        ],
    )
    idx.destroy()


def test_index_add_string_key(idx, full_iscc):
    uid = str(uuid.uuid4())
    idx.add(full_iscc.code, uid)
    assert idx.get_key(full_iscc) == uid


def test_index_query_string_key(idx, full_iscc):
    uid = str(uuid.uuid4())
    idx.add(full_iscc.code, uid)
    r = idx.query(full_iscc)
    assert r.iscc_matches[0].key == uid
