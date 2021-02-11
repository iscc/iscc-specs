# -*- coding: utf-8 -*-
import os
import iscc
from iscc_samples import audios
from iscc import audio
import platform
from tests.test_readables import audio_readables


def test_fpcalc_bin():
    assert "fpcalc" in audio.fpcalc_bin()


def test_fpcalc_is_installed():
    assert isinstance(audio.fpcalc_is_installed(), bool)


def test_download_url():
    url = audio.fpcalc_download_url()
    pl = platform.system().lower()
    pl = "macos" if pl == "darwin" else pl
    assert pl in url
    assert audio.FPCALC_VERSION in url


def test_download():
    out_path = audio.fpcalc_download()
    assert os.path.exists(out_path)


def test_install():
    exe_path = audio.fpcalc_install()
    assert os.path.exists(exe_path)
    assert audio.fpcalc_is_installed()


def test_get_version_info():
    vi = audio.fpcalc_version_info()
    assert vi == audio.FPCALC_VERSION


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
        audio.hash_audio([]).hex()
        == "0000000000000000000000000000000000000000000000000000000000000000"
    )


def test_hash_audio_single():
    assert (
        audio.hash_audio([1]).hex()
        == "0000000100000000000000000000000000000000000000000000000000000000"
    )


def test_hash_audio_short():
    assert (
        audio.hash_audio([1, 2]).hex()
        == "0000000100000002000000000000000000000000000000000000000000000000"
    )


def test_hash_audio_signed():
    assert (
        audio.hash_audio([-1, 0, 1]).hex()
        == "ffffffff00000000000000010000000000000000000000000000000000000000"
    )


def test_code_audio_from_file_path():
    assert iscc.code_audio(audios()[0].as_posix()) == {
        "code": "EIAWUJFCEZVCJIRG",
        "duration": 15.503,
        "title": "Belly Button",
    }


def test_code_audio_from_data():
    assert iscc.code_audio(audios()[0].open("rb").read()) == {
        "code": "EIAWUJFCEZVCJIRG",
        "duration": 15.503,
        "title": "Belly Button",
    }


def test_code_audio_256():
    assert iscc.code_audio(audios()[0].as_posix(), audio_bits=256) == {
        "code": "EIDWUJFCEZVCJIRGNISKEBTKESRAM2REUIDGUJFCEZVCJIRGNISKEJQ",
        "duration": 15.503,
        "title": "Belly Button",
    }


def test_code_audio_granular_short():
    result = iscc.code_audio(
        audios()[0].as_posix(), audio_granular=True, audio_max_duration=5
    )
    assert result == {
        "code": "EIAXRRBCY54IIIWH",
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
                "YmzOgA",
            ],
            "kind": "audio",
        },
        "title": "Belly Button",
    }


def test_code_audio_granular_default():
    result = iscc.code_audio(audios()[0].as_posix(), audio_granular=True)
    assert result == {
        "code": "EIAWUJFCEZVCJIRG",
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
        },
        "title": "Belly Button",
    }
