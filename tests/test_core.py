# -*- coding: utf-8 -*-
import pytest
from iscc import core
from tests import HERE
from os.path import join


SAMPLE = join(HERE, "test.3gp")


def test_compute():
    result = core.compute(SAMPLE)
    assert isinstance(result, dict)
    assert result == {
        "code_meta": "AAA73CA6R4XJLI5C",
        "code_video": "EMAV4DUD6RORW4X4",
        "duration": 60.042,
        "features": [
            "XxqD_x1a8vw",
            "HEqWY8AX9oQ",
            "VA7U9A0f8-w",
            "V5QEfpj-tlQ",
            "dm6ETGUEwmc",
            "vhqD3HFKdtE",
            "Hg4X9f1acng",
            "XkoAn8YVcqU",
            "V06CXFQdUrQ",
            "XBgT_nxD8tE",
        ],
        "fps": 24.0,
        "gmt": "video",
        "height": 144,
        "language": "en",
        "mediatype": "video/mp4",
        "norm_extra": "",
        "norm_title": "kali by anokato spiral sessions 2019",
        "sizes": [7.625, 2.5, 5.083, 1.25, 3.75, 2.792, 15.458, 8.167, 13.042, 0.375],
        "title": "Kali by Anokato - Spiral Sessions 2019",
        "width": 176,
    }
