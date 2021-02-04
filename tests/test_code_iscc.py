# -*- coding: utf-8 -*-
import iscc
import iscc_samples as s


def test_code_iscc_text():
    assert iscc.code_iscc(s.texts()[0]) == {
        "characters": 6077,
        "datahash": "273cbd70856fad155db4c5fddbe6a73fc51b935bafe8251ebad03b83e29eebc7",
        "filename": "demo.doc",
        "filesize": 39936,
        "iscc": "KADQAAK6XRS3QV7TEAASS3POFKWX6MAB2MRNBEZRQVAACJZ4XVYIK3Y",
        "language": "ca",
        "title": "Demo DOC Title from Metadata",
    }


def test_code_iscc_image():
    assert iscc.code_iscc(s.images()[0]) == {
        "datahash": "9db4c0d9e68c5203dc8c2fefe52fa5d54671be3a3253e06888cace7c60e5a743",
        "filename": "demo.bmp",
        "filesize": 53256,
        "height": 133,
        "iscc": "KEDQAAPH5L7RP5X7EEA4GQZQTY6J4MABMAQDAW3M75AADHNUYDM6NDA",
        "title": "demo",
        "width": 200,
    }


def test_code_iscc_audio():
    assert iscc.code_iscc(s.audios()[0]) == {
        "datahash": "1710943a7924bbe4ab67995308742b973e9e452a32277fa8fb077ca024fdee02",
        "duration": 15.5,
        "filename": "demo.aif",
        "filesize": 2734784,
        "iscc": "KIDQAALN53L77D6XEIAWUJFCEZVCIMABYBKLHJ3YWVAACFYQSQ5HSJA",
        "title": "Belly Button",
    }


def test_code_iscc_video():
    assert iscc.code_iscc(s.videos()[0]) == {
        "crop": "352:192:0:46",
        "datahash": "c9a8c0806046de30261e3b31c12e8e8a8392c73e2faae3f822f8913dc6ba0931",
        "duration": 60.042,
        "filename": "demo.3g2",
        "filesize": 1797418,
        "fps": 24.0,
        "height": 288,
        "iscc": "KMDQAAPH5L7RP5X7EMAVNGMC7RMJEMAB5UMGGB7JRVAADSNIYCAGARQ",
        "language": "en",
        "signature_fps": 5,
        "title": "demo",
        "width": 352,
    }


def test_code_iscc_text_granular():
    assert iscc.code_iscc(
        s.texts()[0], text_granular=True, text_avg_chunk_size=512
    ) == {
        "characters": 6077,
        "datahash": "273cbd70856fad155db4c5fddbe6a73fc51b935bafe8251ebad03b83e29eebc7",
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
                "sizes": [1023, 455, 667, 2809, 455, 667, 1],
                "type": "text",
            }
        ],
        "filename": "demo.doc",
        "filesize": 39936,
        "iscc": "KADQAAK6XRS3QV7TEAASS3POFKWX6MAB2MRNBEZRQVAACJZ4XVYIK3Y",
        "language": "ca",
        "title": "Demo DOC Title from Metadata",
    }


def test_code_iscc_audio_granular():
    assert iscc.code_iscc(s.audios()[0], audio_granular=True) == {
        "datahash": "1710943a7924bbe4ab67995308742b973e9e452a32277fa8fb077ca024fdee02",
        "duration": 15.5,
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
                "type": "audio",
            }
        ],
        "filename": "demo.aif",
        "filesize": 2734784,
        "iscc": "KIDQAALN53L77D6XEIAWUJFCEZVCIMABYBKLHJ3YWVAACFYQSQ5HSJA",
        "title": "Belly Button",
    }


def test_code_iscc_video_granular():
    assert iscc.code_iscc(s.videos()[0], video_granular=True) == {
        "crop": "352:192:0:46",
        "datahash": "c9a8c0806046de30261e3b31c12e8e8a8392c73e2faae3f822f8913dc6ba0931",
        "duration": 60.042,
        "features": [
            {
                "features": [
                    "BpbiFpkZg90",
                    "DjsCHB16d_w",
                    "egmyIcKXmyU",
                    "Vo5CVg8cvu0",
                    "Rh7S9A9Yuu0",
                    "Vh_g_g_Qumk",
                    "Rx-AvUCGrk4",
                    "VxqjhNDOpnM",
                    "lJiz5vjultc",
                    "LhoVc1sf0Nk",
                    "Dp4H_fvQ8FE",
                    "Xp8D_fjQ_FM",
                    "RrcjrFhSWlM",
                    "HhQD_fjSVtg",
                    "HRQD_HraVtg",
                    "dAiy5VwZMqw",
                    "aiD2oM49Mqw",
                    "ARoAs9pRAsE",
                    "KpkifcynuHM",
                    "V4yjzFg6GoM",
                    "VyOjjF0aDls",
                    "Fo2ibNyjG1M",
                    "VC2i7vYOC78",
                ],
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
                "type": "video",
            }
        ],
        "filename": "demo.3g2",
        "filesize": 1797418,
        "fps": 24.0,
        "height": 288,
        "iscc": "KMDQAAPH5L7RP5X7EMAVNGMC7RMJEMAB5UMGGB7JRVAADSNIYCAGARQ",
        "language": "en",
        "signature_fps": 5,
        "title": "demo",
        "width": 352,
    }
