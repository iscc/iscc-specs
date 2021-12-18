# -*- coding: utf-8 -*-
import os
from iscc import bin


def test_java_version_info():
    assert 'java' in bin.java_version_info().lower()


def test_ffprobe_bin():
    assert "ffprobe" in bin.ffprobe_bin()


def test_ffprobe_download_url():
    url = bin.ffprobe_download_url()
    assert bin.FFPROBE_VERSION in url


def test_ffprobe_install():
    exe_path = bin.ffprobe_install()
    assert os.path.exists(exe_path)
    assert bin.is_installed(bin.ffprobe_bin())


def test_ffmpeg_install():
    exe_path = bin.ffmpeg_install()
    assert os.path.exists(exe_path)
    assert bin.is_installed(bin.ffmpeg_bin())


def test_ffprobe_get_version_info():
    vi = bin.ffprobe_version_info()
    assert vi == bin.FFPROBE_VERSION
