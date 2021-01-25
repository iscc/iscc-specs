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
    uread_obj=uread(FP),
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
    file.seek(0)
    data = file.read(8)
    assert data.hex() == "0000001866747970"
    assert file.tell() == 8


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_size(uri):
    file = uread(uri)
    file.seek(0)
    assert file.size() == FILE_SIZE
    assert file.tell() == 0


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_filename(uri):
    file = uread(uri)
    assert file.filename in ("test.3gp", "undefined.und")
    file = uread(uri, "customfile.txt")
    assert file.filename == "customfile.txt"


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_mediatype(uri):
    file = uread(uri)
    assert file.mediatype == "video/mp4"


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_puid(uri):
    file = uread(uri)
    assert file.puid == "fmt/199"


def test_uread_context_manager():
    file = open(FP, "rb")
    file.seek(10)
    # don´t close if initiated with open file
    with uread(file) as u:
        u.seek(20)
        assert u.tell() == 20
    assert file.closed == False
    assert file.tell() == 10
    # do close if initiated from file path
    with uread(FP) as u:
        u.read(10)
    assert u._file.closed


@pytest.mark.parametrize("uri", values, ids=ids)
def test_uread_close(uri):
    file = uread(uri)
    assert file.close() == None
