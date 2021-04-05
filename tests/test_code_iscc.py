# -*- coding: utf-8 -*-
import iscc
from iscc.schema import ISCC
import iscc_samples as s


def test_code_iscc_text():
    result = iscc.code_iscc(s.texts()[0])
    assert result == {
        "characters": 6068,
        "datahash": "46d1ebd64f515371c88d1df5bc0d43893b1fa1e58654b2c4244e491d06007a61",
        "filename": "demo.doc",
        "filesize": 40448,
        "gmt": "text",
        "iscc": "KADV4NDFVBLGHAJXFFU64KVNP6UGTAZALCN3HBKABNDND26WJ5IVG4I",
        "language": "ca",
        "mediatype": "application/msword",
        "metahash": "1da548c5285ed35f293c3e22c2f050e037643aae8cf9244b532a162ff5031f52",
        "title": "title from metadata",
        "tophash": "70413571d021a1e0e31ad18d6f8d5b6b0829b0308189ff772e258a0158a70adb",
        "version": "0-0-0",
    }
    assert ISCC(**result)


def test_code_iscc_image():
    result = iscc.code_iscc(s.images()[0])
    assert result == {
        "version": "0-0-0",
        "tophash": "63f6e48bd32d55abe6f05b8d5b99bb2eaf162c47410bcffb7010de00385b71fd",
        "datahash": "9db4c0d9e68c5203dc8c2fefe52fa5d54671be3a3253e06888cace7c60e5a743",
        "filename": "demo.bmp",
        "filesize": 53256,
        "gmt": "image",
        "height": 133,
        "iscc": "KED6P2X7C73P72Z4YNBTBHR4T2HGOYBAGBNWZ767PKO3JQGZ42GFEAY",
        "mediatype": "image/bmp",
        "metahash": "811717648744df4f18656c5f4a833b7b09a90be78205a0e0eeff8b9dbb0202fe",
        "title": "demo",
        "width": 200,
    }
    assert ISCC(**result)


def test_code_iscc_audio():
    result = iscc.code_iscc(s.audios()[0])
    assert result == {
        "version": "0-0-0",
        "tophash": "d20388f25f31bee40baa4895f67b282b68597580edecbb3bcd6c970a934bee7e",
        "datahash": "1710943a7924bbe4ab67995308742b973e9e452a32277fa8fb077ca024fdee02",
        "duration": 15.503,
        "filename": "demo.aif",
        "filesize": 2734784,
        "gmt": "audio",
        "iscc": "KIDW33WX76H5PBHFNISKEJTKESRCNQCUWOTXRNJRMMLRBFB2PESLXZA",
        "mediatype": "audio/aiff",
        "metahash": "c4933dc8c03ea58568159a1cbfb04132c7db93b6b4cd025ffd4db37f52a4756f",
        "title": "Belly Button",
    }
    assert ISCC(**result)


def test_code_iscc_video():
    result = iscc.code_iscc(s.videos()[0])
    assert result == {
        # "crop": "352:192:0:46",
        "version": "0-0-0",
        "tophash": "27afa05e42a2bfd756317f31713b01bd4cad1b768d49c2644dbee53ef0030e5b",
        "datahash": "c9a8c0806046de30261e3b31c12e8e8a8392c73e2faae3f822f8913dc6ba0931",
        "duration": 60.042,
        "filename": "demo.3g2",
        "filesize": 1797418,
        "fps": 24.0,
        "gmt": "video",
        "height": 288,
        "iscc": "KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3PE2RQEAMBDN4MA",
        "language": "en",
        "mediatype": "video/3gpp2",
        "metahash": "811717648744df4f18656c5f4a833b7b09a90be78205a0e0eeff8b9dbb0202fe",
        "title": "demo",
        "width": 352,
    }
    assert ISCC(**result)


def test_code_iscc_text_granular():

    result = iscc.code_iscc(s.texts()[0], text_granular=True, text_avg_chunk_size=512)
    assert result == {
        "characters": 6068,
        "datahash": "46d1ebd64f515371c88d1df5bc0d43893b1fa1e58654b2c4244e491d06007a61",
        "features": [
            {
                "features": [
                    "JUzOuCoesHA",
                    "6eo7KI3_4e8",
                    "aWurLq366Ok",
                    "pWzei6kfs3E",
                    "6eo7KI3_4e8",
                    "aWurLq366Ok",
                    "jp3dJyg55jo",
                ],
                "kind": "text",
                "sizes": [1014, 455, 667, 2809, 455, 667, 1],
                "version": 0,
            }
        ],
        "filename": "demo.doc",
        "filesize": 40448,
        "gmt": "text",
        "iscc": "KADV4NDFVBLGHAJXFFU64KVNP6UGTAZALCN3HBKABNDND26WJ5IVG4I",
        "language": "ca",
        "mediatype": "application/msword",
        "metahash": "1da548c5285ed35f293c3e22c2f050e037643aae8cf9244b532a162ff5031f52",
        "title": "title from metadata",
        "tophash": "70413571d021a1e0e31ad18d6f8d5b6b0829b0308189ff772e258a0158a70adb",
        "version": "0-0-0",
    }
    assert ISCC(**result)


def test_code_iscc_audio_granular():
    result = iscc.code_iscc(s.audios()[0], audio_granular=True)
    assert result == {
        "version": "0-0-0",
        "tophash": "d20388f25f31bee40baa4895f67b282b68597580edecbb3bcd6c970a934bee7e",
        "datahash": "1710943a7924bbe4ab67995308742b973e9e452a32277fa8fb077ca024fdee02",
        "duration": 15.503,
        "features": [
            {
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
            }
        ],
        "filename": "demo.aif",
        "filesize": 2734784,
        "gmt": "audio",
        "iscc": "KIDW33WX76H5PBHFNISKEJTKESRCNQCUWOTXRNJRMMLRBFB2PESLXZA",
        "mediatype": "audio/aiff",
        "metahash": "c4933dc8c03ea58568159a1cbfb04132c7db93b6b4cd025ffd4db37f52a4756f",
        "title": "Belly Button",
    }
    assert ISCC(**result)


def test_code_iscc_video_granular():
    result = iscc.code_iscc(
        s.videos()[0], video_granular=True, video_scenes_ffmpeg=False
    )
    assert result == {
        "datahash": "c9a8c0806046de30261e3b31c12e8e8a8392c73e2faae3f822f8913dc6ba0931",
        "duration": 60.042,
        "features": [
            {
                "features": [
                    "BpbCFpkZgt0",
                    "DjsCHB16dvw",
                    "egmyIIKXmiU",
                    "Vo5CFg8cvu0",
                    "Qh7S9A9Yuu0",
                    "Rh3A_g_Qumk",
                    "Rx-AvUCGrk4",
                    "VxqjhNDOpnM",
                    "lJizwvjultc",
                    "DhoVclMf0Fk",
                    "Dp4H_XvQ8FE",
                    "Xp8D_XjQ_FM",
                    "RrUjjFhSWlM",
                    "HhQD3XjSVtg",
                    "HBQDnDrYVtg",
                    "dAiy5RwZEqw",
                    "aiB2oI49Mqw",
                    "ARoAs5oRAsE",
                    "KpkgfYyjuHM",
                    "VYwizFg6GoM",
                    "VyOjjF0aDgo",
                    "Fo2ibJyjGVM",
                    "VC2i7rYOC78",
                ],
                "kind": "video",
                "sizes": [
                    0.625,
                    7.0,
                    2.5,
                    2.5,
                    2.625,
                    1.25,
                    2.5,
                    1.25,
                    2.75,
                    1.0,
                    3.75,
                    1.75,
                    1.375,
                    3.125,
                    1.625,
                    2.875,
                    1.5,
                    2.75,
                    3.875,
                    1.875,
                    1.0,
                    7.625,
                    2.625,
                ],
                "version": 0,
            }
        ],
        "filename": "demo.3g2",
        "filesize": 1797418,
        "fps": 24.0,
        "gmt": "video",
        "height": 288,
        "iscc": "KMD6P2X7C73P72Z4K2MYF7CYSK5NT3IYMMD6TDPH3PE2RQEAMBDN4MA",
        "language": "en",
        "mediatype": "video/3gpp2",
        "metahash": "811717648744df4f18656c5f4a833b7b09a90be78205a0e0eeff8b9dbb0202fe",
        "title": "demo",
        "tophash": "27afa05e42a2bfd756317f31713b01bd4cad1b768d49c2644dbee53ef0030e5b",
        "version": "0-0-0",
        "width": 352,
    }
    assert ISCC(**result)


def test_code_iscc_video_include_fingerprint():
    r = iscc.code_iscc(s.videos()[0], video_include_fingerprint=True)
    iscc_result_obj = ISCC(**r)
    assert iscc_result_obj.fingerprint.startswith("AAAAAYAAAAAAr4BfgAAAAAAAAJYAAs")
    assert iscc_result_obj.fingerprint.endswith(
        "+vME5VGQ9B5/WvdU+Zjurj60Mkyl0SjSwTWXgks3KxyiL45fM"
    )


def test_code_iscc_text_title_extraction():
    r = iscc.code_iscc(s.texts(".pdf")[0].as_posix())
    assert r["title"] == "title from metadata"
    r = iscc.code_iscc(s.texts(".pdf")[0].as_posix(), title="")
    assert r["title"] == "title from metadata"
