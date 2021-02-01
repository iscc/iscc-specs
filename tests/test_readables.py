# -*- coding: utf-8 -*-
"""Test file and stream handling"""
import io
import mmap
import iscc_samples as s


def get_readables(path_obj):
    raw = path_obj.open("rb").read()
    mmf = path_obj.open("rb")
    mm = mmap.mmap(mmf.fileno(), length=0, access=mmap.ACCESS_READ)
    return [
        raw,  # bytes
        bytearray(raw),  # bytearray
        memoryview(raw),  # memoryview
        path_obj.as_posix(),  # string path
        path_obj,  # path-like
        path_obj.open("rb"),  # file-like
        io.BytesIO(raw),  # BytesIO
        mm,  # Mempory mapped file
    ]


def audio_readables():
    return get_readables(s.audios()[0])


def image_readables():
    return get_readables(s.images()[2])


def text_readables():
    return get_readables(s.texts()[0])


def video_readables():
    return get_readables(s.videos()[4])
