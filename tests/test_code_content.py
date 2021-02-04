# -*- coding: utf-8 -*-
import iscc
import iscc_samples as s


def test_content_code_with_text_defaults():
    tc = iscc.code_content(s.texts()[0])
    assert tc == {
        "code": "EAASS3POFKWX7KDJ",
        "title": "Demo DOC (Title from Metadata)",
        "characters": 6077,
        "language": "ca",
    }


def test_content_code_with_image_defaults():
    tc = iscc.code_content(s.images()[2])
    assert tc == {
        "code": "EEA4GQZQTY6J5DTH",
        "height": 133,
        "title": "Concentrated Cat",
        "width": 200,
    }


def test_content_code_with_audio_defaults():
    tc = iscc.code_content(s.audios()[0])
    assert tc == {"code": "EIAWUJFCEZVCJIRG", "duration": 15.5, "title": "Belly Button"}


def test_content_code_with_video_defaults():
    tc = iscc.code_content(s.videos()[0])
    assert tc == {
        "code": "EMAVNGMC7RMJFOWZ",
        "crop": "352:192:0:46",
        "duration": 60.042,
        "fps": 24.0,
        "height": 288,
        "language": "en",
        "signature_fps": 5,
        "width": 352,
    }
