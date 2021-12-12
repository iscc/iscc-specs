# -*- coding: utf-8 -*-
import iscc
import iscc_samples as s


def test_content_code_with_text_nogran():
    tc = iscc.code_content(s.texts()[0], text_granular=False)
    assert tc == {
        "characters": 6068,
        "iscc": "EAASS2POFKWX7KDJ",
        "gmt": "text",
        "language": "ca",
        "mediatype": "application/msword",
        "title": "title from metadata",
    }


def test_content_code_with_image_nogran():
    tc = iscc.code_content(s.images()[2], image_preview=False, image_granular=False)
    assert tc == {
        "iscc": "EEA4GQZQTY6J5DTH",
        "gmt": "image",
        "height": 133,
        "mediatype": "image/jpeg",
        "title": "Concentrated Cat",
        "width": 200,
    }


def test_content_code_with_audio_nogran():
    tc = iscc.code_content(s.audios()[0], audio_granular=False)
    assert tc == {
        "iscc": "EIAWUJFCEZZOJYVD",
        "duration": 15.503,
        "gmt": "audio",
        "mediatype": "audio/aiff",
        "title": "Belly Button",
    }


def test_content_code_with_video_nogran():
    tc = iscc.code_content(s.videos()[0], video_granular=False, video_preview=False)
    assert tc == {
        "iscc": "EMAVNGMC7RMJFOWZ",
        "duration": 60.146,
        "fps": 24.0,
        "gmt": "video",
        "height": 288,
        "language": "en",
        "mediatype": "video/3gpp2",
        "width": 352,
    }
