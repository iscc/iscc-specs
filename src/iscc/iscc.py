# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
from binascii import hexlify
from statistics import median
import math
from io import BytesIO
from hashlib import sha256
import unicodedata
from PIL import Image
from copy import deepcopy
import xxhash
from iscc.const import *


###############################################################################
# Top-Level functions for generating ISCC Component Codes                     #
###############################################################################


def meta_id(title, extra='', version=0):

    assert version == 0, "Only version 0 supported"

    # 1. Pre-Normalization
    title = text_pre_normalize(title)
    extra = text_pre_normalize(extra)

    # 2. Trimming
    title = text_trim(title)
    extra = text_trim(extra)

    # 3. Concatenate
    concat = '\u0020'.join((title, extra)).strip()

    # 4. Normalization
    normalized = text_normalize(concat)

    # 5. Create a list of n-grams
    n_grams = sliding_window(normalized, width=WINDOW_SIZE_MID)

    # 6. Encode n-grams and create xxhash64-digest
    hash_digests = [xxhash.xxh64(s.encode('utf-8')).digest() for s in n_grams]

    # 7. Apply similarity_hash
    simhash_digest = similarity_hash(hash_digests)

    # 8. Prepend header-byte
    meta_id_digest = HEAD_MID + simhash_digest

    # 9. Encode with base58_iscc
    meta_id = encode(meta_id_digest)

    # 10. Return encoded Meta-ID, trimmed `title` and trimmed `extra` data.
    return [meta_id, title, extra]


def content_id_text(text, partial=False):

    # 1. Pre-normalize
    text = text_pre_normalize(text)

    # 2. Normalize
    text = text_normalize(text)

    # 3. Split to words
    w = text.split()

    # 4. Create 5 word shingles
    shingles = ('\u0020'.join(l) for l in sliding_window(w, WINDOW_SIZE_CID_T))

    # 5. Create 32-bit features with xxHash32
    features = (xxhash.xxh32(s.encode('utf-8')).intdigest() for s in shingles)

    # 6. Apply minimum_hash
    minhash = minimum_hash(features)

    # 7. Collect least significant bits
    lsb = ''.join([str(x & 1) for x in minhash])

    # 8. Create two 64-bit digests
    a = int(lsb[:64], 2).to_bytes(8, 'big', signed=False)
    b = int(lsb[64:], 2).to_bytes(8, 'big', signed=False)

    # 9. Apply simhash to digests
    simhash_digest = similarity_hash((a, b))

    # 10. Prepend component header
    if partial:
        content_id_text_digest = HEAD_CID_T_PCF + simhash_digest
    else:
        content_id_text_digest = HEAD_CID_T + simhash_digest

    # 11. Encode and return
    return encode(content_id_text_digest)


def content_id_image(img, partial=False):

    # 1. Normalize image to 2-dimensional pixel array
    pixels = image_normalize(img)

    # 2. Calculate image hash
    hash_digest = image_hash(pixels)

    # 3. Prepend the 1-byte component header
    if partial:
        content_id_image_digest = HEAD_CID_I_PCF + hash_digest
    else:
        content_id_image_digest = HEAD_CID_I + hash_digest

    # 4. Encode and return
    return encode(content_id_image_digest)


def data_id(data):

    # 1. & 2. XxHash32 over CDC-Chunks
    features = (xxhash.xxh32(chunk).intdigest() for chunk in data_chunks(data))

    # 3. Apply minimum_hash
    minhash = minimum_hash(features)

    # 4. Collect least significant bits
    lsb = ''.join([str(x & 1) for x in minhash])

    # 5. Create two 64-bit digests
    a = int(lsb[:64], 2).to_bytes(8, 'big', signed=False)
    b = int(lsb[64:], 2).to_bytes(8, 'big', signed=False)

    # 6. Apply simhash
    simhash_digest = similarity_hash((a, b))

    # 7. Prepend the 1-byte header
    data_id_digest = HEAD_DID + simhash_digest

    # 8. Encode and return
    return encode(data_id_digest)


def instance_id(data):

    if isinstance(data, str):
        data = open(data, 'rb')

    if not hasattr(data, 'read'):
        data = BytesIO(data)

    leaf_node_digests = []

    while True:
        chunk = data.read(64000)
        if chunk:
            leaf_node_digests.append(sha256d(b'\x00' + chunk))
        else:
            break

    top_hash_digest = top_hash(leaf_node_digests)
    instance_id_digest = HEAD_IID + top_hash_digest[:8]

    code = encode(instance_id_digest)
    hex_hash = hexlify(top_hash_digest).decode('ascii')

    return [code, hex_hash]


###############################################################################
# Content Normalization Functions                                             #
###############################################################################


def text_pre_normalize(text):

    if isinstance(text, bytes):
        text = text.decode('utf-8')
    text = unicodedata.normalize('NFKC', text).strip()

    return text


def text_trim(text):

    while True:
        data = text.encode('utf-8')
        if len(data) <= INPUT_TRIM:
            return text
        else:
            text = text[:-1]


def text_normalize(text):

    # 1. Decompose with NFD
    decomposed = unicodedata.normalize('NFD', text)

    # 2. Filter and normalize
    chars = []
    whitelist = 'LNS'
    for c in decomposed:
        cat = unicodedata.category(c)
        if cat.startswith('Z'):
            if not chars or chars[-1] != '\u0020':
                chars.append('\u0020')
        elif cat[0] in whitelist:
            chars.append(c.lower())

    # 3. Remove leading/trailing whitespace
    filtered_text = ''.join(chars).strip()

    # 4. Re-Compose with NFC
    recomposed = unicodedata.normalize('NFC', filtered_text)

    return recomposed


def image_normalize(img):

    if not isinstance(img, Image.Image):
        img = Image.open(img)

    # 1. Convert to greyscale
    img = img.convert("L")

    # 2. Resize to 32x32
    img = img.resize((32, 32), Image.BICUBIC)

    # 3. Create two dimensional array
    pixels = [
        [list(img.getdata())[32 * i + j] for j in range(32)]
        for i in range(32)
    ]

    return pixels


###############################################################################
# Feature Hashing                                                             #
###############################################################################


def similarity_hash(hash_digests):

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


def minimum_hash(features):

    max_int64 = (1 << 64) - 1
    mersenne_prime = (1 << 61) - 1
    max_hash = (1 << 32) - 1
    hashvalues = [max_hash] * 128
    permutations = deepcopy(MINHASH_PERMUTATIONS)
    a, b = permutations

    for hv in features:
        nhs = []
        for x in range(128):
            nh = (((a[x] * hv + b[x]) & max_int64) % mersenne_prime) & max_hash
            nhs.append(min(nh, hashvalues[x]))
        hashvalues = nhs

    return hashvalues


def image_hash(pixels):
    dct_row_lists = []
    for pixel_list in pixels:
        dct_row_lists.append(dct(pixel_list))

    dct_row_lists_t = list(map(list, zip(*dct_row_lists)))
    dct_col_lists_t = []
    for dct_list in dct_row_lists_t:
        dct_col_lists_t.append(dct(dct_list))

    dct_lists = list(map(list, zip(*dct_col_lists_t)))

    # 5. Extract upper left 8x8 corner
    flat_list = [x for sublist in dct_lists[:8] for x in sublist[:8]]

    # 6. Calculate median
    med = median(flat_list)

    # 7. Create 64-bit digest by comparing to median
    bitstring = ''
    for value in flat_list:
        if value > med:
            bitstring += '1'
        else:
            bitstring += '0'
    hash_digest = int(bitstring, 2).to_bytes(8, 'big', signed=False)

    return hash_digest


def top_hash(hashes):

    size = len(hashes)
    if size == 1:
        return hashes[0]

    pairwise_hashed = []

    for i in range(0, len(hashes) - 1, 2):
        pairwise_hashed.append(hash_inner_nodes(hashes[i], hashes[i + 1]))

    if size % 2 == 1:
        pairwise_hashed.append(hash_inner_nodes(hashes[-1], hashes[-1]))

    return top_hash(pairwise_hashed)


def sha256d(data):

    return sha256(sha256(data).digest()).digest()


def hash_inner_nodes(a, b):

    return sha256d(b'\x01' + a + b)


def data_chunks(data):

    if isinstance(data, str):
        data = open(data, 'rb')

    if not hasattr(data, 'read'):
        data = BytesIO(data)

    section = data.read(GEAR1_MAX)
    counter = 0
    while True:
        if counter < 100:
            if len(section) < GEAR1_MAX:
                section += data.read(GEAR1_MAX)
            if len(section) == 0:
                break
            boundary = chunk_length(
                section,
                GEAR1_NORM,
                GEAR1_MIN,
                GEAR1_MAX,
                GEAR1_MASK1,
                GEAR1_MASK2,
            )
        else:
            if len(section) < GEAR2_MAX:
                section += data.read(GEAR2_MAX)
            if len(section) == 0:
                break
            boundary = chunk_length(
                section,
                GEAR2_NORM,
                GEAR2_MIN,
                GEAR2_MAX,
                GEAR2_MASK1,
                GEAR2_MASK2,
            )

        yield section[:boundary]
        section = section[boundary:]
        counter += 1


def chunk_length(data, norm_size, min_size, max_size, mask_1, mask_2):

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


def sliding_window(seq, width):

    assert width >= 2, "Sliding window width must be 2 or bigger."
    idx = range(max(len(seq) - width + 1, 1))
    return (seq[i:i + width] for i in idx)


def dct(value_list):

    n = len(value_list)
    dct_list = []
    for k in range(n):
        value = 0.0
        for i in range(n):
            value += value_list[i] * math.cos(
                math.pi * k * (2 * i + 1) / (2 * n)
            )
        dct_list.append(2 * value)
    return dct_list


def distance(a, b):

    if isinstance(a, str) and isinstance(b, str):
        a = decode(a)[1:]
        b = decode(b)[1:]

    if isinstance(a, bytes) and isinstance(b, bytes):
        a = int.from_bytes(a, 'big', signed=False)
        b = int.from_bytes(b, 'big', signed=False)

    return bin(a ^ b).count('1')


def encode(digest):

    if len(digest) == 9:
        return encode(digest[:1]) + encode(digest[1:])
    assert len(digest) in (1, 8), "Digest must be 1, 8 or 9 bytes long"
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


def decode(code):

    n = len(code)
    if n == 13:
        return decode(code[:2]) + decode(code[2:])
    if n == 2:
        bit_length = 8
    elif n == 11:
        bit_length = 64
    else:
        raise ValueError('Code must be 2, 11 or 13 chars. Not %s' % n)
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
