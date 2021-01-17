# -*- coding: utf-8 -*-
from iscc.detect import detect
from tests import HERE
from os.path import join


SAMPLE = join(HERE, "test.3gp")


def test_detect_path():
    result = detect(SAMPLE)
    assert result == {"mediatype": "video/mp4", "puid": "fmt/199"}


def test_detect_file():
    with open(SAMPLE, "rb") as infile:
        result = detect(SAMPLE)
    assert result == {"mediatype": "video/mp4", "puid": "fmt/199"}


def test_detect_junk():
    data = b"\xff" * 1024
    result = detect(data)
    assert result == {}
