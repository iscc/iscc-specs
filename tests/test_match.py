# -*- coding: utf-8 -*-
import iscc
from iscc.schema import IsccMatch


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


def test_simple_index_default_name():
    idx = iscc.SimpleIndex()
    assert idx.name == "default"


def test_simple_index_add():
    idx = iscc.SimpleIndex()
    for code in set(TEST_CODES):
        idx.add(code)


def test_simple_index_query():
    idx = iscc.SimpleIndex()
    for code in TEST_CODES:
        idx.add(code)
    idx.add(QUERY_CODE)
    assert idx.query(QUERY_CODE, 3) == [
        IsccMatch(
            key=13,
            iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PSJGVYXJVMT4PF3CSTGC4KNJ4ILI",
            mdist=0,
            cdist=0,
            ddist=0,
            imatch=True,
        ),
        IsccMatch(
            key=4,
            iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PSBWQO33FNHPQNNCY4KHZALJ54JA",
            mdist=0,
            cdist=0,
            ddist=26,
            imatch=False,
        ),
        IsccMatch(
            key=12,
            iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PTKDOPDEUETYGNGGUADC5E5GWOBA",
            mdist=0,
            cdist=0,
            ddist=27,
            imatch=False,
        ),
    ]


def test_simple_split_index_default_name():
    idx = iscc.SimpleSplitIndex()
    assert idx.name == "default"


def test_simple_split_index_membership():
    code = "KIDW33WX76H5PBHFNISKEJTKESRCNYJBCZDNLQXYILWJHQAP3N3KPTQ"
    idx = iscc.SimpleSplitIndex()
    ident = idx.add(code)
    assert ident == 0
    assert "CONTENT-AUDIO-V0-64" in idx.codes
    assert code in idx.isccs.inverse
    assert idx.isccs[0] == code
    assert code in idx
    assert idx.add(code) == ident


def test_simple_split_index_query():
    idx = iscc.SimpleSplitIndex()
    for c in TEST_CODES:
        idx.add(c)
    result = idx.query(QUERY_CODE)
    assert result == [
        IsccMatch(
            iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PSBWQO33FNHPQNNCY4KHZALJ54JA",
            key=4,
            mdist=0,
            cdist=0,
            ddist=26,
            imatch=False,
        ),
        IsccMatch(
            iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PS7G6RNNCWVCAXZFOBG5J3UAB4EA",
            key=10,
            mdist=0,
            cdist=0,
            ddist=31,
            imatch=False,
        ),
        IsccMatch(
            iscc="KMD73CA6R4XJLI5CKYOYF7CYTL5PSDTGHO52LVRXAELT2LOWOCGSFEQ",
            key=11,
            mdist=0,
            cdist=1,
            ddist=37,
            imatch=False,
        ),
        IsccMatch(
            iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PTKDOPDEUETYGNGGUADC5E5GWOBA",
            key=12,
            mdist=0,
            cdist=0,
            ddist=27,
            imatch=False,
        ),
        IsccMatch(
            iscc="KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3PE2RQEAMBDN4MA",
            key=1,
            mdist=28,
            cdist=4,
            ddist=36,
            imatch=False,
        ),
        IsccMatch(
            iscc="KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3NPWULHXP5BXSJI",
            key=2,
            mdist=28,
            cdist=4,
            ddist=36,
            imatch=False,
        ),
        IsccMatch(
            iscc="KMD6P2X7C73P72Z4KYOYF7CYTL5PS5LXYSDEZPZMX65SY36REOETL6Q",
            key=3,
            mdist=28,
            cdist=1,
            ddist=25,
            imatch=False,
        ),
        IsccMatch(
            iscc="KMD6P2X7C73P72Z4KYOYF7CYSL5PTEZDYWYEPFJMWAWTF7WHOUTKTJI",
            key=5,
            mdist=28,
            cdist=0,
            ddist=32,
            imatch=False,
        ),
        IsccMatch(
            iscc="KMD6P2X7C73P72Z4KYOYF7CYSL5PTRJEQGQ3C2MDKRES4YQH223CMQA",
            key=8,
            mdist=28,
            cdist=0,
            ddist=31,
            imatch=False,
        ),
        IsccMatch(
            iscc="KMD6P2X7C73P72Z4KYOYF7CYSL5PSBV2FQQ6IPDDX566E4CQO55IENY",
            key=9,
            mdist=28,
            cdist=0,
            ddist=35,
            imatch=False,
        ),
        IsccMatch(
            iscc="KMD6P2X7C73P72Z4K2PIHNCYLLZPSPNWOCVGDFJNCNDFLFA4BBFYOVY",
            key=7,
            mdist=28,
            cdist=10,
            ddist=35,
            imatch=False,
        ),
    ]
