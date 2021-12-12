# -*- coding: utf-8 -*-
import os

import iscc_core
from iscc_core.code_content_audio import soft_hash_audio_v0

import iscc
from iscc_samples import audios
from iscc import audio
import iscc.bin
import platform
from tests.test_readables import audio_readables


def test_fpcalc_bin():
    assert "fpcalc" in iscc.bin.fpcalc_bin()


def test_fpcalc_is_installed():
    assert isinstance(iscc.bin.fpcalc_is_installed(), bool)


def test_download_url():
    url = iscc.bin.fpcalc_download_url()
    pl = platform.system().lower()
    pl = "macos" if pl == "darwin" else pl
    assert pl in url
    assert iscc.bin.FPCALC_VERSION in url


def test_install():
    exe_path = audio.fpcalc_install()
    assert os.path.exists(exe_path)
    assert iscc.bin.fpcalc_is_installed()


def test_get_version_info():
    vi = iscc.bin.fpcalc_version_info()
    assert vi == iscc.bin.FPCALC_VERSION


def test_extract_audio_features():
    for ar in audio_readables():
        result = audio.extract_audio_features(ar)
        assert result["duration"] == 15.5
        assert result["fingerprint"][:4] == [
            684003877,
            683946551,
            1749295639,
            2017796679,
        ]
        assert result["fingerprint"][-4:] == [
            944185926,
            2026255094,
            2022051494,
            2021919654,
        ]


def test_hash_audio_empty():
    assert (
        soft_hash_audio_v0([]).hex()
        == "0000000000000000000000000000000000000000000000000000000000000000"
    )


def test_hash_audio_single():
    assert (
        soft_hash_audio_v0([1]).hex()
        == "0000000100000001000000000000000000000000000000010000000000000000"
    )


def test_hash_audio_short():
    assert (
        soft_hash_audio_v0([1, 2]).hex()
        == "0000000300000001000000020000000000000000000000010000000200000000"
    )


def test_hash_audio_signed():
    assert (
        soft_hash_audio_v0([-1, 0, 1]).hex()
        == "00000001ffffffff000000000000000100000000ffffffff0000000000000001"
    )


def test_code_audio_from_file_path():
    assert iscc.code_audio(audios()[0].as_posix(), audio_granular=False) == {
        "iscc": "EIAWUJFCEZZOJYVD",
        "duration": 15.503,
        "title": "Belly Button",
    }

# TODO: support audio code from raw data
# def test_code_audio_from_data():
#     assert iscc.code_audio(audios()[0].open("rb").read(), audio_granular=False) == {
#         "iscc": "EIAWUJFCEZZOJYVD",
#         "duration": 15.503,
#         "title": "Belly Button",
#     }


def test_code_audio_256():
    assert iscc.code_audio(
        audios()[0].as_posix(), audio_bits=256, audio_granular=False
    ) == {
        "iscc": "EIDWUJFCEZZOJYVDHJHIRB3KQSQCM2REUITDUTVAQNRGJIRENCCCULY",
        "duration": 15.503,
        "title": "Belly Button",
    }


def test_code_audio_granular_short():
    result = iscc.code_audio(
        audios()[0].as_posix(), audio_granular=True, audio_max_duration=5
    )
    assert result == {
        "iscc": "EIAXRRCKQNUMIMQX",
        "duration": 15.503,
        "features": {
            "features": [
                "KMUSJSjEMjc",
                "aEQiF3hFIkc",
                "eMY21niGSuY",
                "eIVL53iEyKM",
                "eYS4k3rErIM",
                "HgagwxYGwMM",
                "ExZAkhE-QKI",
                "MX5sojH-6aM",
                "c67LgXLty4A",
                "YmzOgAAAAAA",
            ],
            "kind": "audio",
            "version": 0,
        },
        "title": "Belly Button",
    }


def test_code_audio_granular_default():
    result = iscc.code_audio(audios()[0].as_posix(), audio_granular=True)
    assert result == {
        "iscc": "EIAWUJFCEZZOJYVD",
        "duration": 15.503,
        "features": {
            "features": [
                "KMUSJSjEMjc",
                "aEQiF3hFIkc",
                "eMY21niGSuY",
                "eIVL53iEyKM",
                "eYS4k3rErIM",
                "HgagwxYGwMM",
                "ExZAkhE-QKI",
                "MX5sojH-6aM",
                "c67LgXLty4A",
                "YmzOgGJslpA",
                "Ymei4GKloiQ",
                "ZqSyJGbkoiU",
                "ZiTmLm4k7y4",
                "biToLmolWC4",
                "6mYMLur2DA4",
                "a9YkT2mGIE8",
                "aIcjDSjEIh0",
                "OEQiHThEIgc",
                "OEYmVjjGDmY",
                "OIcK5jiMSOc",
                "WIzIoxuMqIM",
                "Hk6kgxYOkIM",
                "Eh6AgxM-wKM",
                "Ez70ozNu7aM",
                "cu7boXLvy5E",
                "YmzLgGIsnpA",
                "YmWioGLloiA",
                "ZqSyJGbksiQ",
                "ZmTiLWYk7i4",
                "biToLm4keC4",
                "6icILutmDA4",
                "6_Y8TmmWJE8",
                "aIYhT2jEIh8",
                "KEQiFzhEIgc",
                "OEYiRjjGHmY",
                "OIYKZjiMSeI",
                "GIzI4hmMqII",
                "Hs6sgxYOoIM",
                "Eh6AgRI-gJE",
                "Ej6AozIurKE",
                "Mm75oXJvy7A",
                "Yi3LkGIsxpA",
                "YmWioGLlomQ",
                "Y6SiJGekkjw",
                "ZmTiHWYk7i4",
                "biTtLm4k6C4",
                "aidMLupmDB4",
                "6_YMDmnWJE4",
                "aYYgT2iFIx8",
                "KMQiHThEIhc",
                "OEciRnjGMvY",
                "eIYOpniEC6Y",
            ],
            "kind": "audio",
            "version": 0,
        },
        "title": "Belly Button",
    }
