# -*- coding: utf-8 -*-
from iscc.detect import detect
import iscc_samples as samples
from tests import HERE
from os.path import join


SAMPLE = join(HERE, "test.3gp")


def test_detect_path():
    result = detect(SAMPLE)
    assert result == {"mediatype": "video/mp4", "puid": "fmt/199"}


def test_detect_file():
    with open(SAMPLE, "rb") as infile:
        result = detect(infile)
        assert infile.tell() == 1337753
    assert result == {"mediatype": "video/mp4", "puid": "fmt/199"}


def test_detect_data():
    with open(SAMPLE, "rb") as infile:
        data = infile.read(1024)
        result = detect(data)
    assert result == {"mediatype": "video/mp4", "puid": "fmt/199"}


def test_detect_junk():
    data = b"\xff" * 1024
    result = detect(data)
    assert result == {}


def test_detect_samples():
    for sample in samples.texts():
        if sample.name != "text.txt":
            assert len(detect(sample)) == 2

    for sample in samples.images():
        assert len(detect(sample)) == 2

    for sample in samples.audios():
        assert len(detect(sample)) == 2

    for sample in samples.videos():
        if sample.name != "demo.3g2":
            assert len(detect(sample)) == 2, sample
