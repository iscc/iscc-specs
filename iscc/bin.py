# -*- coding: utf-8 -*-
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
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
    "windows-64": "5bd8d3d92329861e008555bdab68f5a3556841124eb863de2f2252ca6a0d4f7a",
    "linux-64": "49cd333cf1997799eff7231d3f0ede8830c67413fa7fba09a0c476c430fec38a",
    "osx-64": "96afd9e5462676c6f6c02563eb63f368ecd566b80fc70c7e890346a5a1c65cbd",
}

FFMPEG_VERSION = "4.2.1"
FFMPEG_API_URL = "https://ffbinaries.com/api/v1/version/" + FFMPEG_VERSION
FFMPEG_CHECKSUMS = {
    "windows-64": "7a5ed02a756e5d43cd09360b1cbd3235a08e2d640224f34764af33ed01c50afe",
    "linux-64": "0aeb59f00861e34892086cb4533fbb3a47bfd588d322d736300b5b4ef9beee84",
    "osx-64": "b9e68ad9bc1ed7db39b6002ce34bbe5ab0ac9c501a4613e2ae645e1a4cfc5a12",
}

FPCALC_VERSION = "1.5.1"
FPCALC_URL_BASE = (
    f"https://github.com/acoustid/chromaprint/releases/download/v{FPCALC_VERSION}/"
)

FPCALC_OS_MAP = {
    "Linux": "chromaprint-fpcalc-{}-linux-x86_64.tar.gz".format(FPCALC_VERSION),
    "Darwin": "chromaprint-fpcalc-{}-macos-x86_64.tar.gz".format(FPCALC_VERSION),
    "Windows": "chromaprint-fpcalc-{}-windows-x86_64.zip".format(FPCALC_VERSION),
}
FPCALC_CHECKSUMS = {
    "windows-64": "e29364a879ddf7bea403b0474a556e43f40d525e0d8d5adb81578f1fbf16d9ba",
    "linux-64": "190977d9419daed8a555240b9c6ddf6a12940c5ff470647095ee6242e217de5c",
    "osx-64": "afea164b0bc9b91e5205d126f96a21836a91ea2d24200e1b7612a7304ea3b4f1",
}

TIKA_VERSION = "2.3.0"
TIKA_URL = (
    f"http://archive.apache.org/dist/tika/{TIKA_VERSION}/tika-app-{TIKA_VERSION}.jar"
)
TIKA_CHECKSUM = "e3f6ff0841b9014333fc6de4b849704384abf362100edfa573a6e4104b654491"

EXIV2_VERSION = "0.27.5"
EXIV2_BASE = "http://github.com/Exiv2/exiv2/releases/download/v"
EXIV2_URLS = {
    "windows-64": f"{EXIV2_BASE}{EXIV2_VERSION}/exiv2-{EXIV2_VERSION}-2019msvc64.zip",
    "linux-64": f"{EXIV2_BASE}{EXIV2_VERSION}/exiv2-{EXIV2_VERSION}-Linux64.tar.gz",
    "osx-64": f"{EXIV2_BASE}{EXIV2_VERSION}/exiv2-{EXIV2_VERSION}-Darwin.tar.gz",
}

EXIV2_CHECKSUMS = {
    "windows-64": "3e00112648ed98a60a381fc3c6dd10ec263b1d56dec4f07dce86a7736517ebcd",
    "linux-64": "6c6339f7f575ed794c4669e7eab4ef400a6cf7981f78ea26fc985d24d9620d58",
    "osx-64": "aaf574fa910721fdc653519a2ca8ecf3d4e9b06213167ad630fcb9e18d329af4",
}

EXIV2_RELPATH = {
    "windows-64": f"exiv2-{EXIV2_VERSION}-2019msvc64/bin/exiv2.exe",
    "linux-64": f"exiv2-{EXIV2_VERSION}-Linux64/bin/exiv2",
    "osx-64": f"exiv2-{EXIV2_VERSION}-Darwin/bin/exiv2",
}

EXIV2JSON_RELPATH = {
    "windows-64": f"exiv2-{EXIV2_VERSION}-2019msvc64/bin/exiv2json.exe",
    "linux-64": f"exiv2-{EXIV2_VERSION}-Linux64/bin/exiv2json",
    "osx-64": f"exiv2-{EXIV2_VERSION}-Darwin/bin/exiv2json",
}


def install():
    """Install binary tools for content extraction"""
    exiv2_install()
    fpcalc_install()
    ffprobe_install()
    ffmpeg_install()
    java_install()
    tika_install()


def system_tag():
    os_tag = system().lower()
    if os_tag == "darwin":
        os_tag = "osx"
    os_bits = architecture()[0].rstrip("bit")
    return f"{os_tag}-{os_bits}"


def is_installed(fp: str) -> bool:
    """ "Check if binary at `fp` exists and is executable"""
    return os.path.isfile(fp) and os.access(fp, os.X_OK)


########################################################################################
# Exiv2                                                                                #
########################################################################################


def exiv2_download_url() -> str:
    """Return system and version dependant exiv2 download url"""
    return EXIV2_URLS[system_tag()]


def exiv2_bin() -> str:
    """Returns local path to exiv2 executable."""
    return os.path.join(iscc.APP_DIR, EXIV2_RELPATH[system_tag()])


def exiv2json_bin() -> str:
    return os.path.join(iscc.APP_DIR, EXIV2JSON_RELPATH[system_tag()])


def exiv2_is_installed():
    """Check if exiv2 is installed"""
    fp = exiv2_bin()
    return os.path.isfile(fp) and os.access(fp, os.X_OK)


def exiv2_download():
    b3 = EXIV2_CHECKSUMS[system_tag()]
    return download_file(exiv2_download_url(), checksum=b3)


def exiv2_extract(archive):

    if archive.endswith(".zip"):
        with zipfile.ZipFile(archive, "r") as zip_file:
            zip_file.extractall(Path(archive).parent.absolute())

    elif archive.endswith("tar.gz"):
        with tarfile.open(archive, "r:gz") as tar_file:
            tar_file.extractall(Path(archive).parent.absolute())


def exiv2_install():
    """Install exiv2 command line tool and return path to executable."""
    if exiv2_is_installed():
        log.debug("Exiv2 is already installed.")
        return exiv2_bin()
    log.critical("installing exiv2")
    archive_path = exiv2_download()
    exiv2_extract(archive_path)
    st = os.stat(exiv2_bin())
    os.chmod(exiv2_bin(), st.st_mode | stat.S_IEXEC)
    st = os.stat(exiv2json_bin())
    os.chmod(exiv2json_bin(), st.st_mode | stat.S_IEXEC)

    # macOS workaround to avoid dynamic linking issues
    # Correct way would be to set DYLD_LIBRARY_PATH when calling exiv2,
    # but this makes it easier.
    if system().lower() == "darwin":
        lib_path = Path(exiv2_bin()).parent / ".." / "lib" / "libexiv2.27.dylib"
        lib_bin_path = Path(exiv2_bin()).parent / "libexiv2.27.dylib"
        os.symlink(lib_path, lib_bin_path)

    return exiv2_bin()


def exiv2_version_info():
    """Get exiv2 version info"""
    try:
        r = subprocess.run([exiv2_bin(), "--version"], capture_output=True)
        vi = r.stdout.decode(sys.stdout.encoding)
        return vi
    except FileNotFoundError:
        return "exiv2 not installed"


########################################################################################
# Fpcalc                                                                               #
########################################################################################


def fpcalc_bin():
    """Returns local path to fpcalc executable."""
    if platform.system() == "Windows":
        return os.path.join(iscc.APP_DIR, "fpcalc-{}.exe".format(FPCALC_VERSION))
    return os.path.join(iscc.APP_DIR, "fpcalc-{}".format(FPCALC_VERSION))


def fpcalc_is_installed():
    """ "Check if fpcalc is installed."""
    fp = fpcalc_bin()
    return os.path.isfile(fp) and os.access(fp, os.X_OK)


def fpcalc_download_url():
    """Return system and version dependant download url"""
    return os.path.join(FPCALC_URL_BASE, FPCALC_OS_MAP[platform.system()])


def fpcalc_download():
    """Download fpcalc and return path to archive file."""
    b3 = FPCALC_CHECKSUMS.get(system_tag())
    return download_file(fpcalc_download_url(), checksum=b3)


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


########################################################################################
# ffprobe                                                                              #
########################################################################################


def ffprobe_download_url():
    """Return system dependant download url."""
    urls = requests.get(FFPROBE_API_URL).json()
    return urls["bin"][system_tag()]["ffprobe"]


def ffprobe_bin() -> str:
    """Returns local path to ffprobe executable."""
    path = os.path.join(iscc.APP_DIR, "ffprobe-{}".format(FFPROBE_VERSION))
    if system() == "Windows":
        path += ".exe"
    return path


def ffprobe_download():
    """Download ffprobe and return path to archive file."""
    b3 = FFPROBE_CHECKSUMS.get(system_tag())
    return download_file(ffprobe_download_url(), checksum=b3)


def ffprobe_extract(archive: str):
    """Extract ffprobe from archive."""
    fname = "ffprobe.exe" if system() == "Windows" else "ffprobe"
    with zipfile.ZipFile(archive) as zip_file:
        with zip_file.open(fname) as zf, open(ffprobe_bin(), "wb") as lf:
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


########################################################################################
# ffmpeg                                                                               #
########################################################################################


def ffmpeg_download_url():
    """Return system dependant download url."""
    urls = requests.get(FFPROBE_API_URL).json()
    return urls["bin"][system_tag()]["ffmpeg"]


def ffmpeg_bin() -> str:
    """Returns local path to ffmpeg executable."""
    path = os.path.join(iscc.APP_DIR, "ffmpeg-{}".format(FFMPEG_VERSION))
    if system() == "Windows":
        path += ".exe"
    return path


def ffmpeg_download():
    """Download ffmpeg and return path to archive file."""
    b3 = FFMPEG_CHECKSUMS.get(system_tag())
    return download_file(ffmpeg_download_url(), checksum=b3)


def ffmpeg_extract(archive: str):
    """Extract ffprobe from archive."""
    fname = "ffmpeg.exe" if system() == "Windows" else "ffmpeg"
    with zipfile.ZipFile(archive) as zip_file:
        with zip_file.open(fname) as zf, open(ffmpeg_bin(), "wb") as lf:
            shutil.copyfileobj(zf, lf)


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
    return download_file(tika_download_url(), checksum=TIKA_CHECKSUM)


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


if __name__ == "__main__":
    exiv2_install()
    print(exiv2_version_info())
    # print(java_version_info())
    # print(tika_version_info())
    # print(tika_is_installed())
    # print(tika_install())
    # print(tika_is_installed())
    # print(tika_version_info())
