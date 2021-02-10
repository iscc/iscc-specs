# -*- coding: utf-8 -*-
import pytest
import iscc
import iscc_samples as samples
from collections import OrderedDict
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
def test_mime_guess(uri):
    assert iscc.mime_guess(uri) == "image/jpeg"


def test_mime_guess_readables():
    for readable in image_readables():
        assert iscc.mime_guess(readable) == "image/jpeg"


def test_mime_guess_samples():
    for path in samples.all():
        file_header = path.open(mode="rb").read(4096)
        mt = iscc.mime_guess(file_header)
        assert isinstance(mt, str)
        assert "/" in mt


def test_mime_normalize():
    assert iscc.mime_normalize("audio/x-aiff") == "audio/aiff"


def test_mime_normalize_unmapped():
    assert iscc.mime_normalize("dont/touch/me") == "dont/touch/me"


def test_mime_from_name():
    assert iscc.mime_from_name(SAMPLE.name) == "image/jpeg"


def test_mime_from_data():
    assert iscc.mime_from_data(SAMPLE.read_bytes()) == "image/jpeg"


def test_mime_clean():
    assert iscc.mime_clean("") == ""
    assert iscc.mime_clean("text/html ") == "text/html"
    assert iscc.mime_clean(["text/html", "audio/mp3"]) == "text/html"
    assert iscc.mime_clean([" text/html", "audio/mp3"]) == "text/html"
    assert iscc.mime_clean(" text/plain; charset=windows-1252 ") == "text/plain"
    assert (
        iscc.mime_clean([" text/plain; charset=windows-1252 ", "audio/mp3"])
        == "text/plain"
    )


def test_mime_supported():
    assert iscc.mime_supported("audio/x-aiff") is True
    assert iscc.mime_supported("audio/aiff") is True
    assert iscc.mime_supported("something/unknown") is False
    from iscc.mediatype import SUPPORTED_MEDIATYPES

    for mt in SUPPORTED_MEDIATYPES.keys():
        assert iscc.mime_supported(mt) is True


def test_mime_to_gmt():
    for path in samples.all():
        file_header = path.open(mode="rb").read(4096)
        mt = iscc.mime_guess(file_header)
        gmt = iscc.mime_to_gmt(mt)
        assert gmt in ("text", "image", "audio", "video", None)
