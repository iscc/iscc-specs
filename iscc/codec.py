# -*- coding: utf-8 -*-
"""
The iscc.codec module provides encoding, decoding and transcoding related functions.

ISCC Component Structure:

Header:
    <type> <subtype> <version> <length> each coded as a variable-length 4-bit sequence.
Body:
    <hash-digest>
"""
import math
import os
import enum
import iscc
from base64 import b32encode, b32decode
from typing import Callable, List, Optional, Tuple
from bitarray import bitarray
from bitarray.util import int2ba, ba2int


class MAIN_TYPE(enum.IntEnum):
    """ISCC MainTypes"""
    META = 0
    SEMANTIC = 1
    CONTENT = 2
    DATA = 3
    INSTANCE = 4
    ID = 5
    ISCC = 5

    @property
    def humanized(self):
        return self.name.lower() + '-code'


class SUB_TYPE(enum.IntEnum):
    """Generic SubTypes"""
    NONE = 0


class GMT(enum.IntEnum):
    """Generic Media Types for Content Code"""
    TEXT = 0
    IMAGE = 1
    AUDIO = 2
    VIDEO = 3
    GENERIC = 4
    MIXED = 5


class CHAIN(enum.IntEnum):
    """Chain-ID SubTypes for ISCC-ID"""
    PRIVATE = 0
    BITCOIN = 1
    ETHEREUM = 2
    COBLO = 3
    BLOXBERG = 4


# ISCC Main-Types
MT_MC = 0  #: Meta-Code
MT_SC = 1  #: Semantic-Code
MT_CC = 2  #: Content-Code
MT_DC = 3  #: Data-Code
MT_IC = 4  #: Instance-Code
MT_ID = 5  #: ISCC-ID (Short-ID)
MT_ISCC = 6  #: ISCC-CODE (Fully Qualified ISCC Code)


# ISCC Sub-Types
ST_NONE = 0  #: No Sub-Type

# ISCC Generic Media Sub-Types (for Semantic-Code and Content-Code)
ST_GMT_TXT = 0  #: Sub-Type Text
ST_GMT_IMG = 1  #: Sub-Type Image
ST_GMT_AUD = 2  #: Sub-Type Audio
ST_GMT_VID = 3  #: Sub-Type Video
ST_GMT_GEN = 4  #: Sub-Type Generic
ST_GMT_MIX = 5  #: Sub-Type Mixed

# ISCC Blockchain-IDs SubTypes (for ISCC-ID/Short-ID)
ST_CHAIN_PRV = 0  # Sub-Type for testing or private use (no global uniqueness!!!)
ST_CHAIN_BTC = 1  # Sub-Type Bitcoin
ST_CHAIN_ETH = 2  # Sub-Type Ethereum
ST_CHAIN_CBL = 3  # Sub-Type Content Blockchain
ST_CHAIN_BLX = 4  # Sub-Type Bloxberg


class Header:
    """
    The ISCC-Header has a minimum size of two bytes. It is structured as a sequence
    of nibble (4-bit) based variable-length encoded integers.

    To support forward-compatibility the first bit of each nibble is reserved as a flag
    for a future multi-nibble variable-length encoding.

    The rational behind this scheme is that each element of the header is extensible
    seperately if we are required to accommodate for larger values.
    """

    main_types = {
        MT_MC: "meta-code",
        MT_SC: "semantic-code",
        MT_CC: "content-code",
        MT_DC: "data-code",
        MT_IC: "instance-code",
        MT_ID: "iscc-id",
        MT_ISCC: "iscc-code",
    }

    sub_types = {
        ST_NONE: "none",
    }

    sub_types_cc = {
        ST_GMT_TXT: "text",
        ST_GMT_IMG: "image",
        ST_GMT_AUD: "audio",
        ST_GMT_VID: "video",
    }

    chain_ids = {
        ST_CHAIN_PRV: "private-use",
        ST_CHAIN_BTC: "bitcoin",
        ST_CHAIN_ETH: "ethereum",
        ST_CHAIN_CBL: "coblo",
        ST_CHAIN_BLX: "bloxberg",
    }

    def __init__(
        self,
        m_type: int,
        s_type: int = 0,
        version: int = 0,
        length: Optional[int] = None,
        digest: bytes = b"",
    ):
        if length is None:
            length = len(digest) * 8
        assert m_type in self.main_types, "Unknown MainType with id {}.".format(m_type)
        assert length >= 32, f"Component length {length} must be at least 32bits."
        is_power_of_two = (math.log2(length) - 5).is_integer()
        assert is_power_of_two, f"Component length {length} must be power of two."
        assert length <= 512, "Maximum Component length is 512 bits."
        self.m_type: int = m_type  # ISCC Component Main-Type
        self.s_type: int = s_type  # ISCC Component Sub-Type
        self.version: int = version  # ISCC Component Version
        self.length: int = length  # ISCC Component Length in Bits
        self.digest: bytes = digest  # ISCC

    @classmethod
    def from_bytes(cls, data: bytes):
        """Parses header from 2+ bytes"""
        return cls(*decode_header(data))

    @property
    def bytes(self):
        """Byte-packed representation of header"""
        return bytes(self)

    @property
    def humanized(self):
        """Return a human readable version of the header"""
        if self.m_type == MT_MC:
            s_type_name = self.sub_types[self.s_type]
        elif self.m_type in (MT_CC, MT_ISCC):
            s_type_name = self.sub_types_cc[self.s_type]
        elif self.m_type == MT_ID:
            s_type_name = self.chain_ids[self.s_type]
        else:
            s_type_name = self.sub_types[self.s_type]

        return "{}.{}.{}.{}".format(
            self.main_types[self.m_type],
            s_type_name,
            "v{}".format(self.version),
            "{}bits".format(self.length),
        )

    @property
    def hex(self):
        return self.bytes.hex()

    @property
    def base58_iscc(self):
        return iscc.encode(self.bytes)

    @property
    def bits(self) -> str:
        """Bit-string representation of header"""
        return Bits(self.bytes).bin

    def __bytes__(self):
        """Cast ISCC Header to byte representation"""
        return encode_header(self.m_type, self.s_type, self.version, self.length) + self.digest

    def __str__(self):
        """canonical base32 encoded string representation"""
        return encode_base32(self.bytes)

    def __repr__(self):
        return "ISCC({}, {}, {}, {}, {})".format(
            self.m_type, self.s_type, self.version, self.length, self.digest.hex()
        )


def encode_header(type_: int, subtype: int, version: int = 0, length: int = 64) -> bytes:
    """
    Encodes header values with nibble-sized variable-length encoding.
    The result is minimum 2 and maximum 8 bytes long. If the final count of nibbles
    is uneven it is padded with 4-bit `0000` at the end.
    """
    assert length >= 32 and not length % 32
    length = (length // 32) - 1
    header = bitarray()
    for n in (type_, subtype, version, length):
        header += encode_int(n)
    # Add padding if required
    header.fill()
    return header.tobytes()


def decode_header(data: bytes) -> Tuple:
    """
    Decodes varnibble encoded header and returns it together with remaining bytes.
    :returns: (type, subtype, version, length, remaining bytes)
    """
    result = []
    ba = bitarray()
    ba.frombytes(data)
    data = ba
    for x in range(4):
        value, data = decode_varnibble(data)
        result.append(value)
    # Strip 4-bit padding if required
    if len(data) % 8 and data[:4] == bitarray("0000"):
        data = data[4:]
    result.append(data.tobytes())
    return tuple(result)


def encode_int(n: int) -> bitarray:
    """
    Encode integer to variable length 4-bit sequence.
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


def decode_varnibble(b: bitarray) -> Tuple[int, bitarray]:
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

    raise ValueError("Invalid bitstring")


def encode_base32(digest: bytes) -> str:
    """
    Standard RFC4648 base32 encoding without padding.
    """
    code = b32encode(digest).decode("ascii").rstrip("=")
    return code


def decode_base32(code: str) -> bytes:
    """
    Standard RFC4648 base32 decoding with casefolding.
    """
    return b32decode(code, casefold=True)


def encode_component(digest: bytes, encoder: Callable = encode_base32) -> str:
    """Encode a single ISCC component"""
    return encoder(digest)


def decode_component(code: str, decoder: Callable = decode_base32) -> str:
    """Decode a single ISCC Component"""
    return decoder(code)


if __name__ == "__main__":
    mc = Header(MT_MC, 0, 0, digest=os.urandom(8))
    print()
    print("ISCC:" + str(mc), "->", mc.humanized, "...")

    cid_head = Header(MT_CC, ST_GMT_TXT, 0, 64)
    cid_dig = cid_head.bytes + os.urandom(8)
    print("ISCC:" + encode_base32(cid_dig), "->", cid_head.humanized, "...")
    print(cid_head.base58_iscc)

    did_head = Header(MT_DC, ST_NONE, 0, 64)
    did_dig = did_head.bytes + os.urandom(8)
    print("ISCC:" + encode_base32(did_dig), "->", did_head.humanized, "...")
    print(did_head.base58_iscc)

    iid_head = Header(MT_IC, ST_NONE, 0, 128)
    iid_dig = iid_head.bytes + os.urandom(16)
    print("ISCC:" + encode_base32(iid_dig), "->", iid_head.humanized, "...")
    print(iid_head.base58_iscc)

    id_head = Header(MT_ID, ST_CHAIN_BLX, 0, 32)
    id_dig = iid_head.bytes + os.urandom(4) + b"\x00"
    print("ISCC:" + encode_base32(id_dig), "->", id_head.humanized, "...")
    print(id_head.base58_iscc)

    iscc_head = Header(MT_ISCC, ST_GMT_IMG, 0, 256)
    iscc_dig = iscc_head.bytes + os.urandom(32)
    print("ISCC:" + encode_base32(iscc_dig), "->", iscc_head.humanized, "...")
    print(iscc_head.base58_iscc)

    iscc_head = Header(MT_ISCC, ST_GMT_IMG, 0, 512)
    iscc_dig = iscc_head.bytes + os.urandom(64)
    print("ISCC:" + encode_base32(iscc_dig), "->", iscc_head.humanized, "...")

    print(encode_base32(os.urandom(40)))
    from base64 import standard_b64encode
    print(standard_b64encode((os.urandom(40))))

    print(TYPE(0).humanized)
