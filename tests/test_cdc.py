# -*- coding: utf-8 -*-
from iscc import cdc
from blake3 import blake3
from tests.utils import static_bytes
from tests.test_readables import audio_readables


def test_data_chunks_empty():
    assert list(cdc.data_chunks(b"")) == [b""]


def test_data_chunks_1byte():
    assert list(cdc.data_chunks(b"\x00")) == [b"\x00"]


def test_data_chunks_below_min():
    data = static_bytes(256 - 1)
    assert list(cdc.data_chunks(data)) == [data]


def test_data_chunks_min():
    data = static_bytes(256)
    assert list(cdc.data_chunks(data)) == [data]


def test_data_chunks_above_min():
    data = static_bytes(256 + 1)
    assert list(cdc.data_chunks(data)) == [data]


def test_data_chunks_avg():
    data = static_bytes(1024)
    assert list(cdc.data_chunks(data)) == [data]


def test_data_chunks_avg_above():
    data = static_bytes(1024 + 1)
    assert list(cdc.data_chunks(data)) == [data]


def test_data_chunks_two_chunks():
    data = static_bytes(1024 + 309)
    assert list(cdc.data_chunks(data)) == [data[:-1], data[-1:]]


def test_data_chunks_max_odd():
    expected = [
        "bc0dcea65a2cc750bd1d9b46eb67b6ea54d1fd43088343ceafda3788ac515a31",
        "b6739322973cc1ec27dd70781823187b90159e9739da22d451b3f89b56dd591b",
        "00ff5f6d4895630c9bd76ab4138b3e156707a79589018055305746532bf59f8e",
        "9f261eb3c27561c11aac31475e3ca8d88cafceeb51bae7feb1e8e43794af9760",
        "67f7e7d1d8720581f1b7545a50c320f4814b1d6f7bccba0c911e0ea01788c8fb",
        "1fa982a3d9acfcaedab6e65030ccb2c651b2c2b0f918e9588b22832000c48261",
        "5fae55e1aee84705fc3dc6e831d4f7981677e03338343bd6a783c45e333a55fe",
    ]
    data = static_bytes(8192)
    hashes = [blake3(c).hexdigest() for c in cdc.data_chunks(data)]
    assert len(hashes) == 7
    assert hashes == expected


def test_data_chunks_max_even():
    expected = [
        "bc0dcea65a2cc750bd1d9b46eb67b6ea54d1fd43088343ceafda3788ac515a31",
        "b6739322973cc1ec27dd70781823187b90159e9739da22d451b3f89b56dd591b",
        "00ff5f6d4895630c9bd76ab4138b3e156707a79589018055305746532bf59f8e",
        "9f261eb3c27561c11aac31475e3ca8d88cafceeb51bae7feb1e8e43794af9760",
        "67f7e7d1d8720581f1b7545a50c320f4814b1d6f7bccba0c911e0ea01788c8fb",
        "1fa982a3d9acfcaedab6e65030ccb2c651b2c2b0f918e9588b22832000c48261",
        "25fd35033e2964b02bb5c593b14ff613db663494e709cda3cd388f4f53ec7aca",
        "2032f28cfcdad86090b60fa5cfd8cc44b972df47d5f7e3637001d8e03b8fbc07",
    ]
    data = static_bytes(8192 + 1000)
    hashes = [blake3(c).hexdigest() for c in cdc.data_chunks(data)]
    assert len(hashes) == 8
    assert hashes == expected


def test_data_chunks_stream():
    with open("file_image_lenna.jpg", "rb") as infile:
        chunks1 = list(cdc.data_chunks(infile))
        infile.seek(0)
        chunks2 = list(cdc.data_chunks(infile.read()))
    assert len(chunks1) == 85
    assert len(chunks1[0]) == 438
    assert len(chunks1[-1]) == 255
    assert len(chunks2) == 85
    assert len(chunks2[0]) == 438
    assert len(chunks2[-1]) == 255


def test_get_params():
    assert cdc.get_params(1024) == (256, 8192, 640, 2047, 511)
    assert cdc.get_params(8192) == (2048, 65536, 5120, 16383, 4095)


def test_data_chunks_readables():
    for readable in audio_readables():
        result = list(cdc.data_chunks(readable))
        assert len(result) == 2552
