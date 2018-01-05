# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
import re
import base64
from io import BytesIO
from hashlib import sha256
import unicodedata
from typing import List, ByteString, Sequence, BinaryIO, TypeVar, Generator
import math
from PIL import Image
from iscc.const import CHUNKING_GEAR

# Constants
SYMBOLS = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
VALUES = ''.join([chr(i) for i in range(58)])
C2VTABLE = str.maketrans(SYMBOLS, VALUES)
V2CTABLE = str.maketrans(VALUES, SYMBOLS)
IDTABLE = str.maketrans(SYMBOLS, SYMBOLS)
INPUT_TRIM = 128
B = TypeVar('B', BinaryIO, bytes)

# Component Type Header Markers
HEAD_MID = b'\x00'
HEAD_CID_T = b'\x10'
HEAD_CID_T_PCF = b'\x11'
HEAD_CID_I = b'\x12'
HEAD_CID_I_PCF = b'\x13'
HEAD_CID_A = b'\x14'
HEAD_CID_A_PCF = b'\x15'
HEAD_DID = b'\x20'
HEAD_IID = b'\x30'


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
    simhash_digest = similarity_hash(hash_digests)
    meta_id_digest = HEAD_MID + simhash_digest[:7]

    return base64.b32encode(meta_id_digest).rstrip(b'=').decode('ascii')


def generate_instance_id(data: B) -> str:

    leaf_node_digests = [sha256d(b'\x00' + chunk) for chunk in data_chunks(data)]
    top_hash_digest = top_hash(leaf_node_digests)
    instance_id_digest = HEAD_IID + top_hash_digest[:7]
    return base64.b32encode(instance_id_digest).rstrip(b'=').decode('ascii')


def top_hash(hashes: List[bytes]) -> bytes:

    size = len(hashes)
    if size == 1:
        return hashes[0]

    pairwise_hashed = []

    for i in range(0, len(hashes) - 1, 2):
        pairwise_hashed.append(hash_inner_nodes(hashes[i], hashes[i + 1]))

    if size % 2 == 1:
        pairwise_hashed.append(hash_inner_nodes(hashes[-1], hashes[-1]))

    return top_hash(pairwise_hashed)


def sha256d(data: bytes) -> bytes:
    return sha256(sha256(data).digest()).digest()


def hash_inner_nodes(a: bytes, b: bytes) -> bytes:
    return sha256d(b'\x01' + a + b)


def data_chunks(data: B) -> Generator[bytes, None, None]:

    if not hasattr(data, 'read'):
        data = BytesIO(data)

    section = data.read(640)
    counter = 0
    while True:
        if counter < 100:
            if len(section) < 640:
                section += data.read(640)
            if len(section) == 0:
                break
            boundary = chunk_length(section, 40, 20, 640, 0x016118, 0x00a0b1)
        else:
            if len(section) < 65536:
                section += data.read(65536)
            if len(section) == 0:
                break
            boundary = chunk_length(section, 4096, 2048, 65536, 0x0003590703530000, 0x0000d90003530000)

        yield section[:boundary]
        section = section[boundary:]
        counter += 1


def chunk_length(data: bytes, norm_size: int, min_size: int, max_size: int, mask_1: int, mask_2: int) -> int:
    data_length = len(data)
    i = min_size
    pattern = 0

    if data_length <= min_size:
        return data_length

    while i < min(norm_size, data_length):
        pattern = (pattern << 1) + CHUNKING_GEAR[data[i]]
        if not pattern & mask_1:
            return i
        i = i + 1
    while i < min(max_size, data_length):
        pattern = (pattern << 1) + CHUNKING_GEAR[data[i]]
        if not pattern & mask_2:
            return i
        i = i + 1
    return i


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


def similarity_hash(hash_digests: Sequence[ByteString]) -> ByteString:

    n_bytes = len(hash_digests[0])
    n_bits = (n_bytes * 8)
    vector = [0] * n_bits

    for digest in hash_digests:

        assert len(digest) == n_bytes
        h = int.from_bytes(digest, 'big', signed=False)

        for i in range(n_bits):
            vector[i] += h & 1
            h >>= 1

    minfeatures = len(hash_digests) * 1. / 2
    shash = 0

    for i in range(n_bits):
        shash |= int(vector[i] >= minfeatures) << i

    return shash.to_bytes(n_bytes, 'big', signed=False)


def generate_image_hash(image_path: str) -> str:

    image = Image.open(image_path)
    image = image.convert("L").resize((32, 32), Image.BICUBIC)

    # get image pixels as matrix
    pixels = [[list(image.getdata())[32 * i + j] for j in range(32)] for i in range(32)]

    # discrete cosine transform over every row
    dct_row_lists = []
    for pixel_list in pixels:
        dct_row_lists.append(discrete_cosine_transform(pixel_list))

    # discrete cosine transform over every column
    dct_row_lists_t = list(map(list, zip(*dct_row_lists)))
    dct_col_lists_t = []
    for dct_list in dct_row_lists_t:
        dct_col_lists_t.append(discrete_cosine_transform(dct_list))
    dct_lists = list(map(list, zip(*dct_col_lists_t)))

    # extract upper left 8x7 corner as flat list
    flat_list = [x for sublist in dct_lists[:7] for x in sublist[:8]]

    # compare every value with median and generate hash
    med = sum(sorted(flat_list)[27: 29]) / 2
    hash = ''
    for value in flat_list:
        if value > med:
            hash += '1'
        else:
            hash += '0'
    return hash


def discrete_cosine_transform(value_list: Sequence[float]) -> Sequence[float]:
    N = len(value_list)
    dct_list = []
    for k in range(N):
        value = 0.0
        for n in range(N):
            value += value_list[n] * math.cos(math.pi * k * (2 * n + 1) / (2 * N))
        dct_list.append(2 * value)
    return dct_list


def c2d(code: str) -> ByteString:

    return base64.b32decode(code + '===')


def c2i(code):

    digest = c2d(code)
    return int.from_bytes(digest[1:8], 'big', signed=False)


def hamming_distance(ident1: int, ident2: int) -> int:

    return bin(ident1 ^ ident2).count('1')


def encode(digest: bytes) -> str:
    assert len(digest) == 9, "ISCC component digest must be 9 bytes."
    digest = reversed(digest)
    value = 0
    numvalues = 1
    for octet in digest:
        octet *= numvalues
        value += octet
        numvalues *= 256
    chars = []
    while numvalues > 0:
        chars.append(value % 58)
        value //= 58
        numvalues //= 58
    return str.translate(''.join([chr(c) for c in reversed(chars)]), V2CTABLE)


def decode(code: str) -> bytes:
    assert len(code) == 13, "ISCC component code must be 13 chars."
    bit_length = 72
    code = reversed(str.translate(code, C2VTABLE))
    value = 0
    numvalues = 1
    for c in code:
        c = ord(c)
        c *= numvalues
        value += c
        numvalues *= 58

    numvalues = 2 ** bit_length
    data = []
    while numvalues > 1:
        data.append(value % 256)
        value //= 256
        numvalues //= 256

    return bytes(reversed(data))
