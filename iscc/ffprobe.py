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
DL_API_URL = "https://ffbinaries.com/api/v1/version/" + FFPROBE_VERSION


checksums = {
    "windows-64": "d13e513cbe25df56f2a003740dbfa3c9",
    "linux-64": "d16c0f22a4d86653f9a11ef9da74f644",
    "osx-64": "6cafd5ceede9d4e5bb2a241c9f22efd5",
}


def ffprobe_bin():
    """Returns expected local path to ffprobe executable"""
    path = os.path.join(iscc.APP_DIR, "ffprobe-{}".format(FFPROBE_VERSION))
    if system() == "Windows":
        path += ".exe"
    return path


def ffprobe_is_installed():
    """"Check if ffprobe is installed."""
    fp = ffprobe_bin()
    return os.path.isfile(fp) and os.access(fp, os.X_OK)


def ffprobe_download_url():
    """Return system dependant download url."""
    urls = requests.get(DL_API_URL).json()
    return urls["bin"][system_tag()]["ffprobe"]


def ffprobe_download():
    """Download ffprobe and return path to archive file."""
    md5 = checksums.get(system_tag())
    return download_file(ffprobe_download_url(), md5=md5)


def ffprobe_extract(archive: str):
    """Extract ffprobe from archive."""
    fname = "ffprobe.exe" if system() == "Windows" else "ffprobe"
    with zipfile.ZipFile(archive) as zip_file:
        with zip_file.open(fname) as zf, open(ffprobe_bin(), "wb") as lf:
            shutil.copyfileobj(zf, lf)


def ffprobe_install():
    """Install ffprobe command line tool and return path to executable."""
    if ffprobe_is_installed():
        log.debug("ffprobe is already installed")
        return ffprobe_bin()
    archive_path = ffprobe_download()
    ffprobe_extract(archive_path)
    st = os.stat(ffprobe_bin())
    os.chmod(ffprobe_bin(), st.st_mode | stat.S_IEXEC)
    assert ffprobe_is_installed()
    return ffprobe_bin()


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


def system_tag():
    os_tag = system().lower()
    if os_tag == "darwin":
        os_tag = "osx"
    os_bits = architecture()[0].rstrip("bit")
    return f"{os_tag}-{os_bits}"
