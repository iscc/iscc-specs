# -*- coding: utf-8 -*-
from json import JSONDecodeError
from loguru import logger
import json
import os
import shutil
import subprocess
import platform
import tarfile
import zipfile
import stat
from more_itertools import chunked, windowed
import iscc
from iscc.schema import FeatureType, Options, Readable
from iscc.simhash import similarity_hash
from iscc.utils import download_file
from iscc.codec import encode_base64
from typing import Any, List
from iscc import uread


def hash_audio(features):
    # type: (List[int]) -> bytes
    """Create 256-bit audio similarity hash from chromaprint vector"""
    digests = []
    for int_features in windowed(features, 8, fillvalue=0):
        digest = b""
        for int_feature in int_features:
            digest += int_feature.to_bytes(4, "big", signed=True)
        digests.append(digest)
    shash_digest = similarity_hash(digests)
    return shash_digest


def extract_audio_features(data, **options):
    # type: (Readable, **Any) -> dict
    """Returns Chromaprint fingerprint.

    A dictionary with keys:
    - duration: total duration of extracted fingerprint in seconds (Broken with pipe)
    - fingerprint: 32-bit (4 byte) integers as features
    """
    opts = Options(**options)
    length = str(opts.audio_max_duration)
    file = uread.open_data(data)
    cmd = [fpcalc_bin(), "-raw", "-json", "-signed", "-length", length, "-"]
    res = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=file.read()
    )
    output = res.stdout.decode("utf-8")
    try:
        result = json.loads(output)
    except JSONDecodeError:
        raise RuntimeError(f'Fpcalc error: {res.stderr.decode("utf-8")}')

    return result


def encode_audio_features(features):
    # type: (List[int]) -> dict
    """Pack into 64-bit base encoded features.

    Note: Last feature will be 32-bit if number of features is uneven.
    """
    fingerprints = []
    for int_features in chunked(features, 2):
        digest = b""
        for int_feature in int_features:
            digest += int_feature.to_bytes(4, "big", signed=True)
        fingerprints.append(encode_base64(digest))
    return dict(kind=FeatureType.audio.value, features=fingerprints)


FPCALC_VERSION = "1.5.0"
FPCALC_URL_BASE = (
    f"https://github.com/acoustid/chromaprint/releases/download/v{FPCALC_VERSION}/"
)

FPCALC_OS_MAP = {
    "Linux": "chromaprint-fpcalc-{}-linux-x86_64.tar.gz".format(FPCALC_VERSION),
    "Darwin": "chromaprint-fpcalc-{}-macos-x86_64.tar.gz".format(FPCALC_VERSION),
    "Windows": "chromaprint-fpcalc-{}-windows-x86_64.zip".format(FPCALC_VERSION),
}


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
        logger.debug("Fpcalc is already installed.")
        return fpcalc_bin()
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
