# -*- coding: utf-8 -*-
"""ISCC Reference Implementation"""
import io
from statistics import median
import math
import unicodedata
from PIL import Image
import xxhash
from blake3 import blake3
from more_itertools import interleave, sliced, windowed
from iscc.minhash import minhash_256
from iscc.params import *
from iscc.cdc import data_chunks
from iscc.wtahash import wtahash

###############################################################################
# Top-Level functions for generating ISCC Component Codes                     #
###############################################################################


def meta_id(title, extra=""):

    # 1. Normalization
    title_norm = text_normalize(title)
    extra_norm = text_normalize(extra)

    # 2. Trimming
    title_trimmed = text_trim(title_norm, TRIM_TITLE)
    extra_trimmed = text_trim(extra_norm, TRIM_EXTRA)

    # 3. Simhash title
    title_n_grams = sliding_window(title_trimmed, width=WINDOW_SIZE_MID)
    title_hash_digests = [blake3(s.encode("utf-8")).digest() for s in title_n_grams]
    simhash_digest = similarity_hash(title_hash_digests)

    # 4. Simhash extra metadata
    if extra_trimmed:
        extra_n_grams = sliding_window(extra_trimmed, width=WINDOW_SIZE_MID)
        extra_hash_digests = [blake3(s.encode("utf-8")).digest() for s in extra_n_grams]
        extra_simhash_digest = similarity_hash(extra_hash_digests)
        simhash_digest = b"".join(
            interleave(sliced(simhash_digest, 4), sliced(extra_simhash_digest, 4))
        )

    # 5. Prepend header
    meta_id_digest = HEAD_MID + simhash_digest[:8]

    # 6. Encode with base58_iscc
    code = encode(meta_id_digest)

    # 9. Return encoded Meta-ID, trimmed `title` and trimmed `extra` data and tail.
    return [code, title_trimmed, extra_trimmed]


def content_id_text(text, partial=False, bits=64):

    # 1. Normalize (drop whitespace)
    text = text_normalize(text)

    # 2. Create 13 character n-grams
    ngrams = ("".join(chars) for chars in sliding_window(text, WINDOW_SIZE_CID_T))

    # 3. Create 32-bit features with xxHash32
    features = [xxhash.xxh32_intdigest(s.encode("utf-8")) for s in ngrams]

    # 4. Apply minimum_hash
    digest = minhash_256(features)

    # 6. Encode digest with matching header
    if partial:
        code = encode(HEAD_CID_T_PCF) + encode(digest[: bits // 8])
    else:
        code = encode(HEAD_CID_T) + encode(digest[: bits // 8])

    # 7. Return code
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


def content_id_audio(features, partial=False, bits=64):
    digests = []

    for int_features in windowed(features, 8, fillvalue=0):
        digest = b""
        for int_feature in int_features:
            digest += int_feature.to_bytes(4, "big", signed=True)
        digests.append(digest)
    shash_digest = similarity_hash(digests)
    n_bytes = bits // 8
    if partial:
        content_id_audio_digest = HEAD_CID_A_PCF + shash_digest[:n_bytes]
    else:
        content_id_audio_digest = HEAD_CID_A + shash_digest[:n_bytes]
    return encode(content_id_audio_digest)


def content_id_video(features, partial=False, bits=64):
    sigs = set(features)
    vecsum = [sum(col) for col in zip(*sigs)]
    sh = wtahash(vecsum, hl=bits)
    n_bytes = bits // 8
    if partial:
        content_id_video_digest = HEAD_CID_V_PCF + sh[:n_bytes]
    else:
        content_id_video_digest = HEAD_CID_V + sh[:n_bytes]
    return encode(content_id_video_digest)


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


def data_id(data, bits=64):

    # 1. & 2. XxHash32 over CDC-Chunks
    features = [xxhash.xxh32_intdigest(chunk) for chunk in data_chunks(data)]

    # 3. Apply minimum_hash
    digest = minhash_256(features)

    # 4. Encode with prepended component header
    code = encode(HEAD_DID) + encode(digest[: bits // 8])

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


def text_trim(text, nbytes):
    return text.encode("utf-8")[:nbytes].decode("utf-8", "ignore").strip()


def text_normalize(text):

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

    # 6. Collapse consecutive whitespace
    wsproc_text = " ".join(text_filtered.split())

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
