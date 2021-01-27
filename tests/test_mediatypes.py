# -*- coding: utf-8 -*-
from collections import OrderedDict
import pytest
from iscc import mediatype
import iscc_samples as samples


SAMPLE = samples.texts()[0]
uris = OrderedDict(
    file_path=SAMPLE.as_posix(),
    path_obj=SAMPLE,
    raw_bytes=SAMPLE.read_bytes(),
    file_obj=SAMPLE.open(mode="rb"),
)
values = uris.values()
ids = uris.keys()


@pytest.mark.parametrize("uri", values, ids=ids)
def test_guess(uri):
    assert mediatype.guess(uri) == "application/msword"


def test_from_name():
    assert mediatype.from_name(SAMPLE.name) == "application/msword"


def test_from_data():
    assert mediatype.from_data(SAMPLE.read_bytes()) == "application/msword"


def test_guess_samples():
    for path in samples.all():
        file_header = path.open(mode="rb").read(4096)
        mt = mediatype.guess(file_header)
        assert isinstance(mt, str)
        assert "/" in mt


def test_mime_to_gmt():
    for path in samples.all():
        file_header = path.open(mode="rb").read(4096)
        mt = mediatype.guess(file_header)
        gmt = mediatype.mime_to_gmt(mt)
        assert gmt in ("text", "image", "audio", "video", None)


#
#
# def test_detect_file():
#     with open(SAMPLE, "rb") as infile:
#         result = detect(infile)
#         assert infile.tell() == 0
#     assert result == {
#         "mediatype": "video/mp4",
#     #    "puid": "fmt/199"
#     }
#
#
# def test_detect_data():
#     with open(SAMPLE, "rb") as infile:
#         data = infile.read(1024)
#         result = detect(data)
#     assert result == {
#         "mediatype": "video/mp4",
#     #    "puid": "fmt/199",
#     }
#
#
# def test_detect_samples():
#     for sample in samples.texts():
#         assert len(detect(sample.as_posix())) == 1
#
#     for sample in samples.images():
#         assert len(detect(sample.as_posix())) == 1
#
#     for sample in samples.audios():
#         assert len(detect(sample.as_posix())) == 1
#
#     for sample in samples.videos():
#         assert len(detect(sample.as_posix())) == 1
