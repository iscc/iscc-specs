# -*- coding: utf-8 -*-
"""Functions that measure haming distance of compact binary codes"""
from typing import Union
from bitarray import bitarray
from bitarray.util import count_xor, hex2ba
from iscc.codec import Code, read_header, decode_base32


# ISCC code in various representations
Icode = Union[str, bytes, int, Code]


def distance(a, b):
    # type: (Icode, Icode) -> int
    """Calculate hamming distance for singular ISCC component codes of same type.

    ISCC Codes can be supplied in these formats:
    - Code: a codec.Code object
    - str: base32 encoded ISCC component(including header).
    - bytes: raw byte digest of ISCC component (without header).
    - int: integer representation of ISCC component (without header).
    """
    if isinstance(a, Code):
        return a ^ b
    if isinstance(a, str):
        return distance_code(a, b)
    if isinstance(a, bytes):
        return distance_bytes(a, b)
    if isinstance(a, int):
        return distance_int(a, b)


def distance_code(a, b):
    # type: (str, str) -> int
    """
    Calculate hamming distance for singular ISCC component codes.
    If a string with multiple components is supplied only the first one will be used.
    If components have different length we compute the hamming distance of the shorter
    code with the prefix of the longer code.
    """
    a, b = decode_base32(a), decode_base32(b)
    ha, hb = read_header(a), read_header(b)
    # Byte length of the shorter code
    nbytes = min((ha[3], hb[3])) // 8
    digest_a, digest_b = ha[4][:nbytes], hb[4][:nbytes]
    return distance_bytes(digest_a, digest_b)


def distance_int(a, b):
    # type: (int, int) -> int
    """Calculate hamming dinstance for integer hashes."""
    return bin(a ^ b).count("1")


def distance_bytes(a, b):
    # type: (bytes, bytes) -> int
    """Calculate hamming distance for bytes hash digests."""
    return count_xor(hex2ba(a.hex()), hex2ba(b.hex()))


def distance_hex(a, b):
    # type: (str, str) -> int
    """Calculate hamming distnace for hex encoded hashes."""
    return count_xor(hex2ba(a), hex2ba(b))


def distance_ba(a, b):
    # type: (bitarray, bitarray) -> int
    """Calculate hamming distance for bitarray objects."""
    return count_xor(a, b)
