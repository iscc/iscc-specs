# -*- coding: utf-8 -*-
import iscc
import iscc_samples as s


def test_code_iscc_text():
    assert iscc.code_iscc(s.texts()[0]) == {
        "characters": 6077,
        "datahash": "273cbd70856fad155db4c5fddbe6a73fc51b935bafe8251ebad03b83e29eebc7",
        "filesize": 39936,
        "iscc": "KADQAAK6XRS3QV7TEAASS3POFKWX6MAB2MRNBEZRQVAACJZ4XVYIK3Y",
        "language": "ca",
        "title": "Demo DOC Title from Metadata",
    }


def test_code_iscc_image():
    assert iscc.code_iscc(s.images()[0]) == {
        "datahash": "9db4c0d9e68c5203dc8c2fefe52fa5d54671be3a3253e06888cace7c60e5a743",
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
        "filesize": 2734784,
        "iscc": "KIDQAALN53L77D6XEIAWUJFCEZVCIMABYBKLHJ3YWVAACFYQSQ5HSJA",
        "title": "Belly Button",
    }


def test_code_iscc_video():
    assert iscc.code_iscc(s.videos()[0]) == {
        "crop": "352:192:0:46",
        "datahash": "c9a8c0806046de30261e3b31c12e8e8a8392c73e2faae3f822f8913dc6ba0931",
        "duration": 60.042,
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
    assert iscc.code_iscc(s.texts()[0], text_granular=True) == {
        "characters": 6077,
        "datahash": "273cbd70856fad155db4c5fddbe6a73fc51b935bafe8251ebad03b83e29eebc7",
        "features": ["KW3uKq1_qGk"],
        "filesize": 39936,
        "iscc": "KADQAAK6XRS3QV7TEAASS3POFKWX6MAB2MRNBEZRQVAACJZ4XVYIK3Y",
        "language": "ca",
        "sizes": [6077],
        "title": "Demo DOC Title from Metadata",
    }


def test_code_iscc_audio_granular():
    assert iscc.code_iscc(s.audios()[0], audio_granular=True) == {
        "datahash": "1710943a7924bbe4ab67995308742b973e9e452a32277fa8fb077ca024fdee02",
        "duration": 15.5,
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
            "BjOCHh169_w",
            "Xg8iDIhWv30",
            "Vg7ytg8Yvm0",
            "Rh-C9AXYvm0",
            "Vpqj51COplM",
            "HpgD_3vQ8FE",
            "Xp8D_fjS_NE",
            "HhQDvXrSVtg",
            "XBiCtX4Ydtw",
            "Ypkitd41MtE",
            "QpkivdyjunM",
            "Vi2iDFg7GoM",
            "Fo2ibNyjG1M",
        ],
        "filesize": 1797418,
        "fps": 24.0,
        "height": 288,
        "iscc": "KMDQAAPH5L7RP5X7EMAVNGMC7RMJEMAB5UMGGB7JRVAADSNIYCAGARQ",
        "language": "en",
        "overlap": 3,
        "signature_fps": 5,
        "title": "demo",
        "width": 352,
        "window": 7,
    }
