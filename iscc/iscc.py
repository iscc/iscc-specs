# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
import io
from statistics import median
import math
import unicodedata
from PIL import Image
import xxhash
from blake3 import blake3
from iscc.minhash import minhash
from iscc.params import *
from iscc.cdc import data_chunks


###############################################################################
# Top-Level functions for generating ISCC Component Codes                     #
###############################################################################


def meta_id(title, extra=""):

    # 1. Normalization
    title_norm = text_normalize(title, keep_ws=True)
    extra_norm = text_normalize(extra, keep_ws=True)

    # 2. Trimming
    title_trimmed = text_trim(title_norm)
    extra_trimmed = text_trim(extra_norm)

    # 3. Concatenate
    concat = "\u0020".join((title_trimmed, extra_trimmed)).strip()

    # 4. Create a list of n-grams
    n_grams = sliding_window(concat, width=WINDOW_SIZE_MID)

    # 5. Encode n-grams and create xxhash64-digest
    hash_digests = [xxhash.xxh64(s.encode("utf-8")).digest() for s in n_grams]

    # 6. Apply similarity_hash
    simhash_digest = similarity_hash(hash_digests)

    # 7. Prepend header-byte
    meta_id_digest = HEAD_MID + simhash_digest

    # 8. Encode with base58_iscc
    meta_id = encode(meta_id_digest)

    # 9. Return encoded Meta-ID, trimmed `title` and trimmed `extra` data.
    return [meta_id, title_trimmed, extra_trimmed]


def content_id_text(text, partial=False):

    # 1. Normalize (drop whitespace)
    text = text_normalize(text, keep_ws=False)

    # 2. Create 13 character n-grams
    ngrams = ("".join(l) for l in sliding_window(text, WINDOW_SIZE_CID_T))

    # 3. Create 32-bit features with xxHash32
    features = [xxhash.xxh32_intdigest(s.encode("utf-8")) for s in ngrams]

    # 4. Apply minimum_hash
    minimum_hash = minhash(features)

    # 5. Collect least significant bits of first 64 minhash signatures
    lsb = "".join([str(x & 1) for x in minimum_hash])

    # 6. Create 64-bit digests
    digest = int(lsb, 2).to_bytes(8, "big", signed=False)

    # 7. Encode digest with matching header
    if partial:
        code = encode(HEAD_CID_T_PCF) + encode(digest)
    else:
        code = encode(HEAD_CID_T) + encode(digest)

    # 8. Return code
    return code


def content_id_image(img, partial=False):

    # 1. Normalize image to 2-dimensional pixel array
    pixels = image_normalize(img)

    # 2. Calculate image hash
    hash_digest = image_hash(pixels)

    # 3. Encode with component header
    if partial:
        code = encode(HEAD_CID_I_PCF) + encode(hash_digest)
    else:
        code = encode(HEAD_CID_I) + encode(hash_digest)

    # 4. Return
    return code


def content_id_mixed(cids, partial=False):

    # 1. Decode CIDs
    decoded = (decode(code) for code in cids)

    # 2. Extract first 8-bytes
    truncated = [data[:8] for data in decoded]

    # 3. Apply Similarity hash
    simhash_digest = similarity_hash(truncated)

    # 4. Encode with prepended component header
    if partial:
        code = encode(HEAD_CID_M_PCF) + encode(simhash_digest)
    else:
        code = encode(HEAD_CID_M) + encode(simhash_digest)

    # 5. Return Code
    return code


def data_id(data):

    # 1. & 2. XxHash32 over CDC-Chunks
    features = [xxhash.xxh32_intdigest(chunk) for chunk in data_chunks(data)]

    # 3. Apply minimum_hash
    minimum_hash = minhash(features)

    # 4. Collect least significant bits
    lsb = "".join([str(x & 1) for x in minimum_hash])

    # 5. Create 64-bit digests
    digest = int(lsb, 2).to_bytes(8, "big", signed=False)

    code = encode(HEAD_DID) + encode(digest[:8])
    return code


def instance_id(data):

    # Ensure we have a readable stream
    if isinstance(data, str):
        stream = open(data, "rb")
    elif not hasattr(data, "read"):
        stream = io.BytesIO(data)
    else:
        stream = data

    size = 0
    b3 = blake3()
    while True:
        d = stream.read(IID_READ_SIZE)
        if not d:
            break
        b3.update(d)
        size += len(d)

    top_hash_digest = b3.digest()

    code = encode(HEAD_IID) + encode(top_hash_digest[:8])
    tail = encode(top_hash_digest[8:])

    return [code, tail, size]


###############################################################################
# Content Normalization Functions                                             #
###############################################################################


def text_trim(text):

    return text.encode("utf-8")[:INPUT_TRIM].decode("utf-8", "ignore").strip()


def text_normalize(text, keep_ws=False):

    # 1. Convert bytes to str
    if isinstance(text, bytes):
        text = text.decode("utf-8")

    # 2. Remove leading/trailing whitespace
    text_stripped = text.strip()

    # 3. Lower case
    text_lower = text_stripped.lower()

    # 4. Decompose with NFD
    text_decomposed = unicodedata.normalize("NFD", text_lower)

    # 5. Filter
    chars = []
    for c in text_decomposed:
        cat = unicodedata.category(c)
        if cat not in UNICODE_FILTER:
            chars.append(c)
        elif c in CC_WHITESPACE:
            chars.append(c)
    text_filtered = "".join(chars)

    # 6. Keep or remove whitespace (remove duplicate whitespace)
    if keep_ws:
        wsproc_text = " ".join(text_filtered.split())
    else:
        wsproc_text = "".join(text_filtered.split())

    # 7. Recombine
    recombined = unicodedata.normalize("NFKC", wsproc_text)

    return recombined


def image_normalize(img):

    if not isinstance(img, Image.Image):
        img = Image.open(img)

    # 1. Convert to greyscale
    img = img.convert("L")

    # 2. Resize to 32x32
    img = img.resize((32, 32), Image.BICUBIC)

    # 3. Create two dimensional array
    pixels = [[list(img.getdata())[32 * i + j] for j in range(32)] for i in range(32)]

    return pixels


###############################################################################
# Feature Hashing                                                             #
###############################################################################


def similarity_hash(hash_digests):

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


def image_hash(pixels):

    # 1. DCT per row
    dct_row_lists = []
    for pixel_list in pixels:
        dct_row_lists.append(dct(pixel_list))

    # 2. DCT per col
    dct_row_lists_t = list(map(list, zip(*dct_row_lists)))
    dct_col_lists_t = []
    for dct_list in dct_row_lists_t:
        dct_col_lists_t.append(dct(dct_list))

    dct_lists = list(map(list, zip(*dct_col_lists_t)))

    # 3. Extract upper left 8x8 corner
    flat_list = [x for sublist in dct_lists[:8] for x in sublist[:8]]

    # 4. Calculate median
    med = median(flat_list)

    # 5. Create 64-bit digest by comparing to median
    bitstring = ""
    for value in flat_list:
        if value > med:
            bitstring += "1"
        else:
            bitstring += "0"
    hash_digest = int(bitstring, 2).to_bytes(8, "big", signed=False)

    return hash_digest


def sliding_window(seq, width):

    assert width >= 2, "Sliding window width must be 2 or bigger."
    idx = range(max(len(seq) - width + 1, 1))
    return (seq[i : i + width] for i in idx)


def dct(values_list):
    """
    Discrete cosine transform algorithm by Project Nayuki. (MIT License)
    See: https://www.nayuki.io/page/fast-discrete-cosine-transform-algorithms
    """

    n = len(values_list)
    if n == 1:
        return list(values_list)
    elif n == 0 or n % 2 != 0:
        raise ValueError()
    else:
        half = n // 2
        alpha = [(values_list[i] + values_list[-(i + 1)]) for i in range(half)]
        beta = [
            (values_list[i] - values_list[-(i + 1)])
            / (math.cos((i + 0.5) * math.pi / n) * 2.0)
            for i in range(half)
        ]
        alpha = dct(alpha)
        beta = dct(beta)
        result = []
        for i in range(half - 1):
            result.append(alpha[i])
            result.append(beta[i] + beta[i + 1])
        result.append(alpha[-1])
        result.append(beta[-1])
        return result


def distance(a, b):

    if isinstance(a, str) and isinstance(b, str):
        a = decode(a)[1:]
        b = decode(b)[1:]

    if isinstance(a, bytes) and isinstance(b, bytes):
        a = int.from_bytes(a, "big", signed=False)
        b = int.from_bytes(b, "big", signed=False)

    return bin(a ^ b).count("1")


def encode(digest):

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
    return str.translate("".join([chr(c) for c in reversed(chars)]), V2CTABLE)


def decode(code):

    bit_length = math.floor(math.log(58 ** len(code), 256)) * 8
    n = len(code)

    # TODO remove magic handling of specific code sizes
    if n == 13:
        return decode(code[:2]) + decode(code[2:])

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
