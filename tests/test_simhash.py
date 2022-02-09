# -*- coding: utf-8 -*-
from iscc_core.simhash import similarity_hash


def test_similarity_hash():
    all_zero = 0b0.to_bytes(8, "big")
    assert similarity_hash([all_zero, all_zero]) == all_zero

    all_ones = 0b11111111.to_bytes(1, "big")
    assert similarity_hash([all_ones, all_ones]) == all_ones

    a = 0b0110.to_bytes(1, "big")
    b = 0b1100.to_bytes(1, "big")
    r = 0b1110.to_bytes(1, "big")
    assert similarity_hash([a, b]) == r

    a = 0b01101001.to_bytes(1, "big")
    b = 0b00111000.to_bytes(1, "big")
    c = 0b11100100.to_bytes(1, "big")
    r = 0b01101000.to_bytes(1, "big")
    assert similarity_hash([a, b, c]) == r

    a = 0b01100101.to_bytes(1, "big")
    b = 0b01011001.to_bytes(1, "big")
    c = 0b10010101.to_bytes(1, "big")
    d = 0b10101001.to_bytes(1, "big")
    r = 0b11111101.to_bytes(1, "big")
    assert similarity_hash([a, b, c, d]) == r

    a = 0b0110100101101001.to_bytes(2, "big")
    b = 0b0011100000111000.to_bytes(2, "big")
    c = 0b1110010011100100.to_bytes(2, "big")
    r = 0b0110100001101000.to_bytes(2, "big")
    assert similarity_hash([a, b, c]) == r
