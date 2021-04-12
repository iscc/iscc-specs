# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import zipfile
from platform import system, architecture
import requests
from loguru import logger as log
import iscc
from iscc.utils import download_file
import stat


FFPROBE_VERSION = "4.2.1"
FFPROBE_API_URL = "https://ffbinaries.com/api/v1/version/" + FFPROBE_VERSION
FFPROBE_CHECKSUMS = {
    "windows-64": "d13e513cbe25df56f2a003740dbfa3c9",
    "linux-64": "d16c0f22a4d86653f9a11ef9da74f644",
    "osx-64": "6cafd5ceede9d4e5bb2a241c9f22efd5",
}

FFMPEG_VERSION = "4.2.1"
FFMPEG_API_URL = "https://ffbinaries.com/api/v1/version/" + FFMPEG_VERSION
FFMPEG_CHECKSUMS = {
    "windows-64": "6d5dc6d2bb579ac3f78fda858f07bc5b",
    "linux-64": "01fb50166b77dd128dca786fe152ac2c",
    "osx-64": "c882209d862e33e9dc4f7abe1adb5e1b",
}


def ffprobe_bin() -> str:
    """Returns local path to ffprobe executable."""
    path = os.path.join(iscc.APP_DIR, "ffprobe-{}".format(FFPROBE_VERSION))
    if system() == "Windows":
        path += ".exe"
    return path


def ffmpeg_bin() -> str:
    """Returns local path to ffmpeg executable."""
    path = os.path.join(iscc.APP_DIR, "ffmpeg-{}".format(FFMPEG_VERSION))
    if system() == "Windows":
        path += ".exe"
    return path


def is_installed(fp: str) -> bool:
    """"Check if binary at `fp` exists and is executable"""
    return os.path.isfile(fp) and os.access(fp, os.X_OK)


def ffprobe_download_url():
    """Return system dependant download url."""
    urls = requests.get(FFPROBE_API_URL).json()
    return urls["bin"][system_tag()]["ffprobe"]


def ffmpeg_download_url():
    """Return system dependant download url."""
    urls = requests.get(FFPROBE_API_URL).json()
    return urls["bin"][system_tag()]["ffmpeg"]


def ffprobe_download():
    """Download ffprobe and return path to archive file."""
    md5 = FFPROBE_CHECKSUMS.get(system_tag())
    return download_file(ffprobe_download_url(), md5=md5)


def ffmpeg_download():
    """Download ffmpeg and return path to archive file."""
    md5 = FFMPEG_CHECKSUMS.get(system_tag())
    return download_file(ffmpeg_download_url(), md5=md5)


def ffprobe_extract(archive: str):
    """Extract ffprobe from archive."""
    fname = "ffprobe.exe" if system() == "Windows" else "ffprobe"
    with zipfile.ZipFile(archive) as zip_file:
        with zip_file.open(fname) as zf, open(ffprobe_bin(), "wb") as lf:
            shutil.copyfileobj(zf, lf)


def ffmpeg_extract(archive: str):
    """Extract ffprobe from archive."""
    fname = "ffmpeg.exe" if system() == "Windows" else "ffmpeg"
    with zipfile.ZipFile(archive) as zip_file:
        with zip_file.open(fname) as zf, open(ffmpeg_bin(), "wb") as lf:
            shutil.copyfileobj(zf, lf)


def ffprobe_install():
    """Install ffprobe command line tool and return path to executable."""
    if is_installed(ffprobe_bin()):
        log.debug("ffprobe is already installed")
        return ffprobe_bin()
    archive_path = ffprobe_download()
    ffprobe_extract(archive_path)
    st = os.stat(ffprobe_bin())
    os.chmod(ffprobe_bin(), st.st_mode | stat.S_IEXEC)
    assert is_installed(ffprobe_bin())
    return ffprobe_bin()


def ffmpeg_install():
    """Install ffmpeg command line tool and return path to executable."""
    if is_installed(ffmpeg_bin()):
        log.debug("ffmpeg is already installed")
        return ffmpeg_bin()
    archive_path = ffmpeg_download()
    ffmpeg_extract(archive_path)
    st = os.stat(ffmpeg_bin())
    os.chmod(ffmpeg_bin(), st.st_mode | stat.S_IEXEC)
    assert is_installed(ffmpeg_bin())
    return ffmpeg_bin()


def ffprobe_version_info():
    """Get ffprobe version"""
    try:
        r = subprocess.run([ffprobe_bin(), "-version"], stdout=subprocess.PIPE)
        return (
            r.stdout.decode("utf-8")
            .strip()
            .splitlines()[0]
            .split()[2]
            .rstrip("-static")
        )
    except FileNotFoundError:
        return "ffprobe not installed"


def ffmpeg_version_info():
    """Get ffmpeg version"""
    try:
        r = subprocess.run([ffmpeg_bin(), "-version"], stdout=subprocess.PIPE)
        return (
            r.stdout.decode("utf-8")
            .strip()
            .splitlines()[0]
            .split()[2]
            .rstrip("-static")
        )
    except FileNotFoundError:
        return "ffmpeg not installed"


def system_tag():
    os_tag = system().lower()
    if os_tag == "darwin":
        os_tag = "osx"
    os_bits = architecture()[0].rstrip("bit")
    return f"{os_tag}-{os_bits}"


if __name__ == "__main__":
    ffmpeg_install()
    print(ffmpeg_version_info())
