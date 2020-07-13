# -*- coding: utf-8 -*-
"""
Merkle Tree

Simple merkle tree implementation on top of blake3.
Compatible with https://pypi.org/project/pymerkle/ v2.0.2
"""
import io
from binascii import hexlify
from blake3 import blake3
from iscc.slide import multi_slide


LEAF_SIZE = 262144


def tophash(data):
    hash, size = tophash_size(data)
    return hash.hex()


def tophash_size(data):
    if isinstance(data, str):
        stream = open(data, "rb")
    elif not hasattr(data, "read"):
        stream = io.BytesIO(data)
    else:
        stream = data

    tree, size = merkletree(stream)
    return tree[-1][0], size


def merkletree(stream):
    levels = []
    leaves = []
    size = 0

    chunk = stream.read(LEAF_SIZE)
    size = len(chunk)

    while chunk:
        leaves.append(blake3(b"\x00" + chunk).digest())
        chunk = stream.read(LEAF_SIZE)
        size += len(chunk)

    levels.append(leaves)

    while len(leaves) > 1:
        leaves = pairwise_hash(leaves)
        levels.append(leaves)

    return levels, size


def pairwise_hash(leaves):
    result = []
    for a, b in multi_slide(leaves, 2, 2):
        if not b:
            new = a
        else:
            new = blake3(b"\01" + hexlify(a) + b"\01" + hexlify(b)).digest()
        result.append(new)
    return result
