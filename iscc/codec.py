# -*- coding: utf-8 -*-
"""
The iscc.codec module provides encoding, decoding and transcoding related functions.

ISCC Component Structure:

Header:
    <type> <subtype> <version> <length> each coded as a variable-length 4-bit sequence.
Body:
    <hash-digest> with number of bits as indicated byi <length>
"""
import base64
import enum
from typing import Tuple
from bitarray import bitarray
from bitarray.util import int2ba, ba2int
from bech32 import convertbits


BASE32_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


class MT(enum.IntEnum):
    """ISCC Main Types"""

    META = 0
    SEMANTIC = 1
    CONTENT = 2
    DATA = 3
    INSTANCE = 4

    @property
    def humanized(self):
        return self.name.lower() + "-code"


class ST(enum.IntEnum):
    """Generic SubTypes"""

    NONE = 0


class ST_CC(enum.IntEnum):
    """SubTypes for Content Codes"""

    TEXT = 0
    IMAGE = 1
    AUDIO = 2
    VIDEO = 3
    GENERIC = 4
    MIXED = 5


class VS(enum.IntEnum):
    """ISCC code Versions"""

    V0 = 0


def write_header(mtype: int, stype: int, version: int = 0, length: int = 64) -> bytes:
    """
    Encodes header values with nibble-sized variable-length encoding.
    The result is minimum 2 and maximum 8 bytes long. If the final count of nibbles
    is uneven it is padded with 4-bit `0000` at the end.
    """
    assert length >= 32 and not length % 32, "Length must be a multiple of 32"
    length = (length // 32) - 1
    header = bitarray()
    for n in (mtype, stype, version, length):
        header += _write_varnibble(n)
    # Add padding if required
    header.fill()
    return header.tobytes()


def read_header(data: bytes) -> Tuple[int, int, int, int, bytes]:
    """
    Decodes varnibble encoded header and returns it together with remaining bytes.
    :returns: (type, subtype, version, length, remaining bytes)
    """
    result = []
    ba = bitarray()
    ba.frombytes(data)
    data = ba
    for x in range(3):
        value, data = _read_varnibble(data)
        result.append(value)

    # interpret length value
    length, data = _read_varnibble(data)
    result.append((length + 1) * 32)

    # Strip 4-bit padding if required
    if len(data) % 8 and data[:4] == bitarray("0000"):
        data = data[4:]

    result.append(data.tobytes())

    return tuple(result)


def encode_base32(data: bytes) -> str:
    """
    Standard RFC4648 base32 encoding without padding.
    """
    b32 = convertbits(data, 8, 5, True)
    return "".join([BASE32_CHARSET[c] for c in b32])


def decode_base32(code: str) -> bytes:
    """
    Standard RFC4648 base32 decoding without padding and with casefolding.
    """
    code = code.upper()
    data = [BASE32_CHARSET.find(c) for c in code]
    dec = convertbits(data, 5, 8, False)
    return bytes(dec)


def encode_base64(data: bytes) -> str:
    """
    Standard RFC4648 base64url encoding without padding.
    """
    code = base64.urlsafe_b64encode(data).decode("ascii")
    return code.rstrip("=")


def decode_base64(code: str) -> bytes:
    """
    Standard RFC4648 base64url decoding without padding.
    """
    padding = 4 - (len(code) % 4)
    string = code + ("=" * padding)
    return base64.urlsafe_b64decode(string)


def _write_varnibble(n: int) -> bitarray:
    """
    Writes integer to variable length 4-bit sequence.
    Variable-length encoding scheme:
    ------------------------------------------------------
    | prefix bits | nibbles | data bits | unsigned range |
    | ----------- | ------- | --------- | -------------- |
    | 0           | 1       | 3         | 0 - 7          |
    | 10          | 2       | 6         | 8 - 71         |
    | 110         | 3       | 9         | 72 - 583       |
    | 1110        | 4       | 12        | 584 - 4679     |
    ------------------------------------------------------
    """
    if 0 <= n < 8:
        return int2ba(n, length=4)
    elif 8 <= n < 72:
        return bitarray("10") + int2ba(n - 8, length=6)
    elif 72 <= n < 584:
        return bitarray("110") + int2ba(n - 72, length=9)
    elif 584 <= n < 4680:
        return bitarray("1110") + int2ba(n - 584, length=12)
    else:
        raise ValueError("Value must be between 0 and 4679")


def _read_varnibble(b: bitarray) -> Tuple[int, bitarray]:
    """Reads first varnibble, returns its integer value and remaining bits."""

    bits = len(b)

    if bits >= 4 and b[0] == 0:
        return ba2int(b[:4]), b[4:]
    if bits >= 8 and b[1] == 0:
        return ba2int(b[2:8]) + 8, b[8:]
    if bits >= 12 and b[2] == 0:
        return ba2int(b[3:12]) + 72, b[12:]
    if bits >= 16 and b[3] == 0:
        return ba2int(b[4:16]) + 584, b[16:]

    raise ValueError("Invalid bitarray")
