# -*- coding: utf-8 -*-
import iscc
import xxhash
from iscc.cdc import data_chunks


# Average number of characters per text chunk
AVG_SIZE_TEXT = 1024
NGRAM_SIZE = 13


def text_chunks(text: str, avg_size=AVG_SIZE_TEXT):
    """
    Generates variable sized text chunks (without leading BOM)
    """
    data = text.encode("utf-32-be")
    avg_size *= 4  # 4 bytes per character
    for chunk in data_chunks(data, avg_size=avg_size, utf32=True):
        yield chunk.decode("utf-32-be")


def text_fingerprint(text: str, avg_size=AVG_SIZE_TEXT, ngram_size=NGRAM_SIZE):
    """
    Create granular fingerprint for text (minhashes over cdc-chunks)

    :param str text: Normalized plaintext.
    :param avg_size: Average chunk size vor detail hashes.
    :param ngram_size: Sliding windows widht in number of characters.

    """
    chunks = text_chunks(text, avg_size=avg_size)
    fingerprint = []
    for chunk in chunks:
        ngrams = ("".join(chars) for chars in iscc.sliding_window(chunk, ngram_size))
        features = [xxhash.xxh32_intdigest(s.encode("utf-8")) for s in ngrams]
        minimum_hash = iscc.minhash_256(features)
        fingerprint.append(minimum_hash[:8].hex())
    return fingerprint


if __name__ == "__main__":
    """
    Basic usage to create granular fingerprints for text (hex coded for now).
    These granular fingerprints can be matched via exact matches of granular
    fingerprints or with a small hamming-distance threshold.
    """
    from fauxfactory.factories.strings import gen_utf8

    text = gen_utf8(1024 * 100)
    norm_text = iscc.text_normalize(text)
    fp = text_fingerprint(norm_text, 1024, 13)
    print(len(fp))
    print(fp)
