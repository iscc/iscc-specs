# -*- coding: utf-8 -*-
import iscc
from iscc.match import Match


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


def test_simple_index_membership():
    code = "KIDW33WX76H5PBHFNISKEJTKESRCNYJBCZDNLQXYILWJHQAP3N3KPTQ"
    idx = iscc.SimpleIndex()
    ident = idx.add(code)
    assert ident == 0
    assert "CONTENT-AUDIO-V0-64" in idx.codes
    assert code in idx.isccs.inverse
    assert idx.isccs[0] == code
    assert code in idx
    assert idx.add(code) == ident


def test_simple_index_query():
    idx = iscc.SimpleIndex()
    for c in TEST_CODES:
        idx.add(c)
    result = idx.query(QUERY_CODE)
    assert result == [
        Match(
            ident=4,
            iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PSBWQO33FNHPQNNCY4KHZALJ54JA",
            type="META-NONE-V0-64",
            distance=0,
        ),
        Match(
            ident=10,
            iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PS7G6RNNCWVCAXZFOBG5J3UAB4EA",
            type="META-NONE-V0-64",
            distance=0,
        ),
        Match(
            ident=11,
            iscc="KMD73CA6R4XJLI5CKYOYF7CYTL5PSDTGHO52LVRXAELT2LOWOCGSFEQ",
            type="META-NONE-V0-64",
            distance=0,
        ),
        Match(
            ident=12,
            iscc="KMD73CA6R4XJLI5CKYOYF7CYSL5PTKDOPDEUETYGNGGUADC5E5GWOBA",
            type="META-NONE-V0-64",
            distance=0,
        ),
        Match(
            ident=1,
            iscc="KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3PE2RQEAMBDN4MA",
            type="CONTENT-VIDEO-V0-64",
            distance=4,
        ),
        Match(
            ident=2,
            iscc="KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3NPWULHXP5BXSJI",
            type="CONTENT-VIDEO-V0-64",
            distance=4,
        ),
        Match(
            ident=3,
            iscc="KMD6P2X7C73P72Z4KYOYF7CYTL5PS5LXYSDEZPZMX65SY36REOETL6Q",
            type="CONTENT-VIDEO-V0-64",
            distance=1,
        ),
        Match(
            ident=5,
            iscc="KMD6P2X7C73P72Z4KYOYF7CYSL5PTEZDYWYEPFJMWAWTF7WHOUTKTJI",
            type="CONTENT-VIDEO-V0-64",
            distance=0,
        ),
        Match(
            ident=8,
            iscc="KMD6P2X7C73P72Z4KYOYF7CYSL5PTRJEQGQ3C2MDKRES4YQH223CMQA",
            type="CONTENT-VIDEO-V0-64",
            distance=0,
        ),
        Match(
            ident=9,
            iscc="KMD6P2X7C73P72Z4KYOYF7CYSL5PSBV2FQQ6IPDDX566E4CQO55IENY",
            type="CONTENT-VIDEO-V0-64",
            distance=0,
        ),
        Match(
            ident=7,
            iscc="KMD6P2X7C73P72Z4K2PIHNCYLLZPSPNWOCVGDFJNCNDFLFA4BBFYOVY",
            type="CONTENT-VIDEO-V0-64",
            distance=10,
        ),
    ]
