# -*- coding: utf-8 -*-
import os
from iscc import ffprobe


def test_ffprobe_bin():
    assert "ffprobe" in ffprobe.ffprobe_bin()


def test_ffprobe_is_installed():
    assert isinstance(ffprobe.ffprobe_is_installed(), bool)


def test_ffprobe_download_url():
    url = ffprobe.ffprobe_download_url()
    assert ffprobe.FFPROBE_VERSION in url


def test_ffprobe_install():
    exe_path = ffprobe.ffprobe_install()
    assert os.path.exists(exe_path)
    assert ffprobe.ffprobe_is_installed()


def test_ffprobe_get_version_info():
    vi = ffprobe.ffprobe_version_info()
    assert vi == ffprobe.FFPROBE_VERSION
