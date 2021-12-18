# -*- coding: utf-8 -*-
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from platform import system, architecture
import requests
from loguru import logger as log
import iscc
from iscc.utils import download_file
import stat
import jdk


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

FPCALC_VERSION = "1.5.0"
FPCALC_URL_BASE = (
    f"https://github.com/acoustid/chromaprint/releases/download/v{FPCALC_VERSION}/"
)

FPCALC_OS_MAP = {
    "Linux": "chromaprint-fpcalc-{}-linux-x86_64.tar.gz".format(FPCALC_VERSION),
    "Darwin": "chromaprint-fpcalc-{}-macos-x86_64.tar.gz".format(FPCALC_VERSION),
    "Windows": "chromaprint-fpcalc-{}-windows-x86_64.zip".format(FPCALC_VERSION),
}

TIKA_VERSION = "2.2.0"
TIKA_URL = f"https://dlcdn.apache.org/tika/{TIKA_VERSION}/tika-app-{TIKA_VERSION}.jar"
TIKA_CHECKSUM = "62ba528230481c9917f2dcbf3524e63d"


def install():
    """Install binary tools for content extraction"""
    fpcalc_install()
    ffprobe_install()
    ffmpeg_install()
    java_install()
    tika_install()


def fpcalc_bin():
    """Returns local path to fpcalc executable."""
    if platform.system() == "Windows":
        return os.path.join(iscc.APP_DIR, "fpcalc-{}.exe".format(FPCALC_VERSION))
    return os.path.join(iscc.APP_DIR, "fpcalc-{}".format(FPCALC_VERSION))


def fpcalc_is_installed():
    """"Check if fpcalc is installed."""
    fp = fpcalc_bin()
    return os.path.isfile(fp) and os.access(fp, os.X_OK)


def fpcalc_download_url():
    """Return system and version dependant download url"""
    return os.path.join(FPCALC_URL_BASE, FPCALC_OS_MAP[platform.system()])


def fpcalc_download():
    """Download fpcalc and return path to archive file."""
    return download_file(fpcalc_download_url())


def fpcalc_extract(archive):
    """Extract archive with fpcalc executable."""
    if archive.endswith(".zip"):
        with zipfile.ZipFile(archive, "r") as zip_file:
            for member in zip_file.namelist():
                filename = os.path.basename(member)
                if filename == "fpcalc.exe":
                    source = zip_file.open(member)
                    target = open(fpcalc_bin(), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
    elif archive.endswith("tar.gz"):
        with tarfile.open(archive, "r:gz") as tar_file:
            for member in tar_file.getmembers():
                if member.isfile() and member.name.endswith("fpcalc"):
                    source = tar_file.extractfile(member)
                    target = open(fpcalc_bin(), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)


def fpcalc_install():
    """Install fpcalc command line tool and return path to executable."""
    if fpcalc_is_installed():
        log.debug("Fpcalc is already installed.")
        return fpcalc_bin()
    log.critical("installing fpcalc")
    archive_path = fpcalc_download()
    fpcalc_extract(archive_path)
    st = os.stat(fpcalc_bin())
    os.chmod(fpcalc_bin(), st.st_mode | stat.S_IEXEC)
    assert fpcalc_is_installed()
    return fpcalc_bin()


def fpcalc_version_info():
    """Get fpcalc version"""
    try:
        r = subprocess.run([fpcalc_bin(), "-v"], stdout=subprocess.PIPE)
        return r.stdout.decode("utf-8").strip().split()[2]
    except FileNotFoundError:
        return "FPCALC not installed"


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
    log.critical("installing ffprobe")
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
    log.critical("installing ffmpeg")
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
            .rstrip("-tessu")
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
            .rstrip("-tessu")
        )
    except FileNotFoundError:
        return "ffmpeg not installed"


########################################################################################
# Java                                                                                 #
########################################################################################


def java_bin():
    java_path = shutil.which("java")
    if not java_path:
        java_path = java_custom_path()
    return java_path


def java_custom_path():
    if platform.system() == "Windows":
        java_path = os.path.join(iscc.APP_DIR, "jdk-16.0.2+7-jre", "bin", "java.exe")
    else:
        java_path = os.path.join(iscc.APP_DIR, "jdk-16.0.2+7-jre", "bin", "java")
    return java_path


def java_is_installed():
    return bool(shutil.which("java")) or is_installed(java_custom_path())


def java_install():
    if java_is_installed():
        log.debug("java already installed")
        return java_bin()
    log.critical("installing java")
    return jdk.install("16", impl="openj9", jre=True, path=iscc.APP_DIR)


def java_version_info():
    try:
        r = subprocess.run([java_bin(), "-version"], stderr=subprocess.PIPE)
        return r.stderr.decode(sys.stdout.encoding).splitlines()[0]
    except subprocess.CalledProcessError:
        return "JAVA not installed"


########################################################################################
# Apache Tika                                                                          #
########################################################################################


def tika_bin():
    # type: () -> str
    """Returns path to java tika app call"""
    return os.path.join(iscc.APP_DIR, f"tika-app-{TIKA_VERSION}.jar")


def tika_is_installed():
    # type: () -> bool
    """Check if tika is installed"""
    return os.path.exists(tika_bin())


def tika_download_url():
    # type: () -> str
    """Return tika download url"""
    return TIKA_URL


def tika_download():
    # type: () -> str
    """Download tika-app.jar and return local path"""
    return download_file(tika_download_url(), md5=TIKA_CHECKSUM)


def tika_install():
    # type: () -> str
    """Install tika-app.jar if not installed yet."""
    # Ensure JAVA is installed
    java_install()

    if tika_is_installed():
        log.debug("Tika is already installed")
        return tika_bin()
    else:
        log.critical("installing tika")
        path = tika_download()
        st = os.stat(tika_bin())
        os.chmod(tika_bin(), st.st_mode | stat.S_IEXEC)
        return path


def tika_version_info():
    # type: () -> str
    """
    Check tika-app version

    :return: Tika version info string
    :rtype: str
    """
    try:
        r = subprocess.run(
            [java_bin(), "-jar", tika_bin(), "--version"], stdout=subprocess.PIPE
        )
        return r.stdout.decode(sys.stdout.encoding).strip()
    except subprocess.CalledProcessError:
        return "Tika not installed"


def system_tag():
    os_tag = system().lower()
    if os_tag == "darwin":
        os_tag = "osx"
    os_bits = architecture()[0].rstrip("bit")
    return f"{os_tag}-{os_bits}"


if __name__ == "__main__":
    print(java_version_info())
    print(tika_version_info())
    # print(tika_is_installed())
    # print(tika_install())
    # print(tika_is_installed())
    # print(tika_version_info())
