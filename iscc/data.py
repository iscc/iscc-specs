# -*- coding: utf-8 -*-
"""Fuction for similarity preserving Data-Code."""
from loguru import logger as log
from typing import Any, Tuple, List
import xxhash
from codetiming import Timer
from more_itertools import chunked
from iscc_core.cdc import data_chunks
from iscc.minhash import minhash_64, minhash_256
from iscc.codec import encode_base64
from iscc.schema import FeatureType, Readable, Options


def hash_data(data):
    _, features = extract_data_features(data)
    return hash_data_features(features)


def hash_data_features(features):
    # type: (List[int]) -> bytes
    """Create 256-bit data similarity hash from data-chunk int32 hashes"""
    with Timer(text="data feature minhashing took {:0.4f}s", logger=log.debug):
        return minhash_256(features)


def extract_data_features(data, **options):
    # type: (Readable, **Any) -> Tuple[List[int], List[int]]
    """Extract low level data features (chunk-sizes, int32-hashes)"""
    opts = Options(**options)
    features = []
    sizes = []
    with Timer(text="data features extraction took {:0.4f}s", logger=log.debug):
        for chunk in data_chunks(data, **opts.dict()):
            sizes.append(len(chunk))
            features.append(xxhash.xxh32_intdigest(chunk))
    return sizes, features


def encode_data_features(sizes, features, **options):
    # type: (List[int], List[int], **Any) -> dict
    """Reduce and encode low level features.

    :return: dicttionary with {"sizes": ..., "features": ...}
    """
    opts = Options(**options)
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
