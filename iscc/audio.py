# -*- coding: utf-8 -*-
from json import JSONDecodeError
import json
import subprocess
from more_itertools import chunked
from iscc.bin import fpcalc_bin, fpcalc_install
from iscc.schema import FeatureType, Options, Readable
from iscc.codec import encode_base64
from typing import Any, List
from iscc import uread


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
    try:
        res = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=file.read()
        )
    except FileNotFoundError:
        fpcalc_install()
        file.seek(0)
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
    if len(features) % 2 != 0:
        features.append(0)
    fingerprints = []
    for int_features in chunked(features, 2):
        digest = b""
        for int_feature in int_features:
            digest += int_feature.to_bytes(4, "big", signed=True)
        fingerprints.append(encode_base64(digest))
    return dict(kind=FeatureType.audio.value, version=0, features=fingerprints)
