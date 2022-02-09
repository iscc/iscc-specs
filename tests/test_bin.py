# -*- coding: utf-8 -*-
import os
from iscc import bin


def test_java_version_info():
    vi = bin.java_version_info().lower()
    assert "java" in vi or "openjdk" in vi
    assert len(vi.splitlines()) == 1


def test_tika_version_info():
    bin.java_install()
    bin.tika_install()
    vi = bin.tika_version_info().lower()
    assert "tika" in vi
    assert len(vi.splitlines()) == 1


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
    assert bin.FFPROBE_VERSION in vi


def test_exiv2_download_url():
    durl = bin.exiv2_download_url()
    assert durl.startswith("http://github.com/Exiv2/exiv2/releases")
    assert bin.EXIV2_VERSION in durl


def test_exiv2_bin():
    bpath = bin.exiv2_bin()
    assert os.path.basename(bpath).startswith("exiv2")


def test_exiv2_install():
    bin.exiv2_install()
    assert bin.exiv2_is_installed()


def test_exiv2_version_info():
    vs = bin.exiv2_version_info()
    assert "exiv2" in vs.lower()
