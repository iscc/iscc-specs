# -*- coding: utf-8 -*-
"""Fuctione for Data-Code granular fingerprints."""
from loguru import logger as log
from typing import Any, List
from codetiming import Timer
from more_itertools import chunked
from iscc_core.minhash import minhash_64
from iscc_core.codec import encode_base64
from iscc.schema import FeatureType
from iscc.options import SdkOptions


def encode_data_features(sizes, features, **options):
    # type: (List[int], List[int], **Any) -> dict
    """Reduce and encode low level features.

    :return: dicttionary with {"sizes": ..., "features": ...}
    """
    opts = SdkOptions(**options)
    with Timer(text="data features encoding took {:0.4f}s", logger=log.debug):
        encoded_sizes = [sum(fh) for fh in chunked(sizes, opts.data_granular_factor)]
        encoded_features = [
            encode_base64(minhash_64(cf))
            for cf in chunked(features, opts.data_granular_factor)
        ]
    return dict(
        kind=FeatureType.data.value,
        version=0,
        features=encoded_features,
        sizes=encoded_sizes,
    )
