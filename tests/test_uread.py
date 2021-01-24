# -*- coding: utf-8 -*-
import pytest
from pathlib import Path
from tests import HERE
from os.path import join
from iscc.uread import uread
from collections import OrderedDict

FP = join(HERE, "test.3gp")
FILE_SIZE = 1337753


uris = OrderedDict(
    file_path=FP,
    path_obj=Path(FP),
    raw_bytes=open(FP, "rb").read(),
    file_obj=open(FP, "rb"),
    mem_view=memoryview(open(FP, "rb").read()),
)

values = uris.values()
ids = uris.keys()


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_tell(uri):
    file = uread(uri)
    assert file.tell() == 0


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_seek(uri):
    file = uread(uri)
    file.seek(10)
    assert file.tell() == 10


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_read(uri):
    file = uread(uri)
    data = file.read(8)
    assert data.hex() == "0000001866747970"
    assert file.tell() == 8


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_size(uri):
    file = uread(uri)
    assert file.size == FILE_SIZE
    assert file.tell() == 0


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_filename(uri):
    file = uread(uri)
    assert file.filename in ("test.3gp", "undefined.und")
    file = uread(uri, "customfile.txt")
    assert file.filename == "customfile.txt"


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_view(uri):
    file = uread(uri)
    assert file.tell() == 0
    view = file.view()
    view.seek(10)
    assert view.tell() == 10
    assert file.tell() == 0
    view.close()


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_mediatype(uri):
    file = uread(uri)
    assert file.mediatype == "video/mp4"


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_puid(uri):
    file = uread(uri)
    assert file.puid == "fmt/199"


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_close(uri):
    file = uread(uri)
    assert file.close() == None
