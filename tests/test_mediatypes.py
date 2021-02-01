# -*- coding: utf-8 -*-
from collections import OrderedDict
import pytest
from iscc import mediatype
import iscc_samples as samples

from tests.test_readables import image_readables


SAMPLE = samples.images()[2]
uris = OrderedDict(
    file_path=SAMPLE.as_posix(),
    path_obj=SAMPLE,
    raw_bytes=SAMPLE.read_bytes(),
    file_obj=SAMPLE.open(mode="rb"),
)
values = uris.values()
ids = uris.keys()


@pytest.mark.parametrize("uri", values, ids=ids)
def test_guess_mediatype(uri):
    assert mediatype.guess_mediatype(uri) == "image/jpeg"


def test_guess_mediatype_readables():
    for readable in image_readables():
        assert mediatype.guess_mediatype(readable) == "image/jpeg"


def test_from_name():
    assert mediatype.from_name(SAMPLE.name) == "image/jpeg"


def test_from_data():
    assert mediatype.from_data(SAMPLE.read_bytes()) == "image/jpeg"


def test_guess_samples():
    for path in samples.all():
        file_header = path.open(mode="rb").read(4096)
        mt = mediatype.guess_mediatype(file_header)
        assert isinstance(mt, str)
        assert "/" in mt


def test_mime_to_gmt():
    for path in samples.all():
        file_header = path.open(mode="rb").read(4096)
        mt = mediatype.guess_mediatype(file_header)
        gmt = mediatype.mime_to_gmt(mt)
        assert gmt in ("text", "image", "audio", "video", None)
