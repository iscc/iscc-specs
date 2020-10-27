# -*- coding: utf-8 -*-
"""
The iscc.codec module provides encoding, decoding and transcoding related functions.

ISCC Component Structure:

Header:
    <type> <subtype> <version> <length> each coded as a variable-length 4-bit sequence.
Body:
    <hash-digest>
"""
import os
import iscc
from base64 import b32encode, b32decode
from typing import Callable, Tuple
from bitstring import Bits


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

# Base32 Alphabet
BASE32_STANDARD = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
BASE32_ISCC = "MBSGCFDHIJKLANRPQOETUVWXYZ234567"
S2I = str.maketrans(BASE32_STANDARD, BASE32_ISCC)
I2S = str.maketrans(BASE32_ISCC, BASE32_STANDARD)


class ISCCHeader:
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
        self, m_type: int, s_type: int = 0, version: int = 0, length: int = 64
    ):
        assert m_type in self.main_types, "Unknown MainType with id {}.".format(m_type)
        assert (
            length % 32 == 0
        ), f"Component length {length} must be a multiple of 32 bits."
        assert length <= 256, "Maximum Component length is currently 256 bits."
        self.m_type: int = m_type  # ISCC Component Main-Type
        self.s_type: int = s_type  # ISCC Component Sub-Type
        self.version: int = version  # ISCC Component Version
        self.length: int = length  # ISCC Component Length in Bits

    @classmethod
    def from_bytes(cls, data: bytes):
        """Parses header from 2+ bytes"""
        return cls(*unpack_header(data))

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
        """Cast to ISCC Header to byte representation"""
        mt = pack_int(self.m_type)
        st = pack_int(self.s_type)
        ve = pack_int(self.version)
        le = pack_int(self.length // 32 - 1)
        return (mt + st + ve + le).tobytes()

    def __str__(self):
        """canonical base32 encoded string representation"""
        return encode_base32(self.bytes + os.urandom(8))

    def __repr__(self):
        return "ISCCHeader({}, {}, {}, {})".format(
            self.m_type, self.s_type, self.version, self.length
        )


def pack_int(n: int) -> Bits:
    """Pack positive integer into nibble sized bitvector"""
    assert 8 > n >= 0, "Multi-nibble packing not yet supported. N must be between 0 & 7"
    return Bits(uint=n, length=4)


def unpack_header(data: bytes) -> Tuple[int, int, int, int]:
    """Unpack component header to type, subtype, version, length indexes"""
    bits = Bits(bytes=data[:2], length=16)
    main_type = bits[0:4].uint
    sub_type = bits[4:8].uint
    version = bits[8:12].uint
    length = bits[12:16].uint * 32
    return main_type, sub_type, version, length


def encode_base32(digest: bytes) -> str:
    """
    Standard RFC4648 base32 encoding without padding and with custom alphabet.
    """
    code = b32encode(digest).decode("ascii").rstrip("=")
    return code.translate(S2I)


def decode_base32(code: str) -> bytes:
    """
    Standard RFC4648 base32 decoding with casefolding.
    """
    code = code.upper().translate(I2S)
    return b32decode(code, casefold=True)


def encode_component(digest: bytes, encoder: Callable = encode_base32) -> str:
    """Encode a single ISCC component"""
    return encoder(digest)


def decode_component(code: str, decoder: Callable = decode_base32) -> str:
    """Decode a single ISCC Component"""
    return decoder(code)


if __name__ == "__main__":
    mc_head = ISCCHeader(MT_MC, 0, 0, 64)
    mc_dig = mc_head.bytes + os.urandom(8)
    print(encode_base32(mc_dig), "->", mc_head.humanized, "...")

    cid_head = ISCCHeader(MT_CC, ST_GMT_TXT, 0, 64)
    cid_dig = cid_head.bytes + os.urandom(8)
    print(encode_base32(cid_dig), "->", cid_head.humanized, "...")

    did_head = ISCCHeader(MT_DC, ST_NONE, 0, 64)
    did_dig = did_head.bytes + os.urandom(8)
    print(encode_base32(did_dig), "->", did_head.humanized, "...")

    iid_head = ISCCHeader(MT_IC, ST_NONE, 0, 128)
    iid_dig = iid_head.bytes + os.urandom(16)
    print(encode_base32(iid_dig), "->", iid_head.humanized, "...")

    id_head = ISCCHeader(MT_ID, ST_CHAIN_BTC, 0, 32)
    id_dig = iid_head.bytes + os.urandom(4) + b"\x00"
    print(encode_base32(id_dig), "->", id_head.humanized, "...")

    iscc_head = ISCCHeader(MT_ISCC, ST_GMT_IMG, 0, 256)
    iscc_dig = iscc_head.bytes + os.urandom(32)
    print(encode_base32(iscc_dig), "->", iscc_head.humanized, "...")

    composit = mc_dig + cid_dig + did_dig + iid_dig[:10]
    print(encode_base32(composit))
