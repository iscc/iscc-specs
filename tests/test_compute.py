# -*- coding: utf-8 -*-
from iscc import compute
from tests import HERE
from os.path import join


SAMPLE = join(HERE, "test.3gp")


def test_compute():
    result = compute.compute(SAMPLE)
    assert isinstance(result, dict)
    assert result == {
        "code": "EMAV4DUC6QORW4X4",
        "code_data": "GAA2Q3TYZFBE6BTJ",
        "code_instance": "IAAY2QAMLUTU2ZYE",
        "code_meta": "AAA73CA6R4XJLI5C",
        "datahash": "8d400c5d274d670476eb3e62d199c172084ea0760f65d8566f0a9aa19c335610",
        "duration": 60.042,
        "features": [
            "XxqT9x1a8vw",
            "HGqWS0AW8oQ",
            "Vg7U9A0esuw",
            "VgYGfgj2tmQ",
            "dw6FTHUE4nU",
            "vhqD3XVSdtE",
            "Hg4X9f1acvg",
            "XkoAn8YVcqU",
            "V06CXBQdUrU",
        ],
        "filesize": 1337753,
        "fps": 24.0,
        "gmt": "video",
        "height": 144,
        "language": "en",
        "mediatype": "video/mp4",
        "signature_fps": 5,
        "sizes": [7.625, 2.5, 5.083, 1.25, 3.75, 2.792, 15.458, 8.167, 13.042],
        "title": "Kali by Anokato - Spiral Sessions 2019",
        "width": 176,
    }
