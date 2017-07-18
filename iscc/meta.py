# -*- coding: utf-8 -*-
import re
import base64
from hashlib import sha256
import unicodedata
from typing import List, ByteString, Sequence

# Magic Constants

INPUT_TRIM = 128


def generate_meta_id(title: str, creators: str='', extra: str='', version: int=0) -> str:

    assert version == 0, "Only version 1 supported"

    title, creators, extra = trim(title, creators, extra)

    title = normalize_text(title)
    creators = normalize_creators(creators)
    extra = normalize_text(extra)

    concat = '\u0020'.join((title, creators, extra)).rstrip('\u007C')

    a = sliding_window(concat, width=2) * 3
    b = sliding_window(concat, width=3) * 2
    c = sliding_window(concat, width=4)
    n_grams = a + b + c

    hash_digests = [sha256(s.encode('utf-8')).digest() for s in n_grams]

    simhash_digest = simhash(hash_digests)
    prefix = b'\x00'
    suffix = simhash_digest[:7]
    meta_id_digest = prefix + suffix
    meta_id_code = base64.b32encode(meta_id_digest).rstrip(b'=').decode('ascii')

    return meta_id_code


def normalize_text(text: str) -> str:

    whitelist = 'LNS'
    decomposed = unicodedata.normalize('NFD', text)
    chars = []

    for c in decomposed:
        cat = unicodedata.category(c)
        if cat.startswith('Z'):
            chars.append(' ')
        elif cat[0] in whitelist:
            chars.append(c.lower())

    filtered = ''.join(chars)
    collapsed = '\u0020'.join(filtered.split())
    normalized = unicodedata.normalize('NFC', collapsed)

    return normalized


def normalize_creators(text: str) -> str:

    nonum = re.sub("\d+", "", text, flags=re.UNICODE)

    creators = []

    for creator in nonum.split(';'):

        if ',' in creator:
            creator = ' '.join(reversed(creator.split(',')[:2]))
        ncreators = normalize_text(creator)

        tokens = ncreators.split()
        if not tokens:
            continue
        if tokens[0] == tokens[-1]:
            abridged = tokens[0]
        else:
            abridged = tokens[0][0] + tokens[-1]
        creators.append(abridged)

    return '\u0020'.join(sorted(creators))


def trim(*text: str) -> List[str]:

    trimmed = []
    for t in text:
        trimmed.append(unicodedata.normalize('NFKC', t)[:INPUT_TRIM])
    return trimmed


def sliding_window(text: str, width: int) -> List:

    assert width >= 2, "Sliding window width must be 2 or bigger."
    idx = range(max(len(text) - width + 1, 1))
    return [text[i:i + width] for i in idx]


def simhash(hash_digests: Sequence[ByteString]) -> ByteString:

    n_bytes = len(hash_digests[0])
    hashbits = (n_bytes * 8)

    vector = [0] * hashbits
    for token in hash_digests:

        assert len(token) == n_bytes, 'All digests must have the same number of bytes'

        h = int.from_bytes(token, 'big', signed=False)

        for i in range(hashbits):
            vector[i] += h & 1
            h >>= 1

    minfeatures = len(hash_digests) * 1. / 2

    shash = 0
    for i in range(hashbits):
        shash |= int(vector[i] >= minfeatures) << i

    return shash.to_bytes(n_bytes, 'big', signed=False)


def c2d(code: str) -> ByteString:

    return base64.b32decode(code + '===')


def c2i(code):

    digest = c2d(code)
    return int.from_bytes(digest[1:8], 'big', signed=False)


def hamming_distance(ident1: int, ident2: int) -> int:

    return bin(ident1 ^ ident2).count('1')


def jaccard_similarity(ident1, ident2):
    """Bitwise jaccard coefficient of integers a, b"""
    and_bits = bin(ident1 & ident2).count("1")
    xor_bits = bin(ident1 ^ ident2).count("1")
    return 1 - xor_bits / (and_bits + xor_bits)
