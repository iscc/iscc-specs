# -*- coding: utf-8 -*-
from typing import Sequence


def similarity_hash(hash_digests):
    # type: (Sequence[bytes]) -> bytes
    """
    Creates a similarity preserving hash from a sequence of equal sized hash digests.
    """

    n_bytes = len(hash_digests[0])
    n_bits = n_bytes * 8
    vector = [0] * n_bits

    for digest in hash_digests:
        h = int.from_bytes(digest, "big", signed=False)

        for i in range(n_bits):
            vector[i] += h & 1
            h >>= 1

    minfeatures = len(hash_digests) * 1.0 / 2
    shash = 0

    for i in range(n_bits):
        shash |= int(vector[i] >= minfeatures) << i

    return shash.to_bytes(n_bytes, "big", signed=False)
