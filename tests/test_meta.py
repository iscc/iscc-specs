# -*- coding: utf-8 -*-
from iscc import meta


def test_generate_meta_id():

    mid1 = meta.generate_meta_id('Die Unendliche Geschichte', 'Michael Ende')
    assert len(mid1) == 13
    assert mid1 == 'AB2GMJUABNYWW'

    mid2 = meta.generate_meta_id('Die Unendliche Geschichte', 'Ende, Michael')
    assert mid1 == mid2

    mid3 = meta.generate_meta_id('Die Unéndliche Geschichte', 'Ende, M.')
    assert mid1 == mid3


def test_normalize_text():

    text = 'Iñtërnâtiônàlizætiøn☃💩 is a ticky \u00A0 thing'
    normalized = meta.normalize_text(text)
    assert normalized == 'internationalizætiøn☃💩 is a ticky thing'


def test_normalize_creators():
    nc = meta.normalize_creators
    assert nc('') == ''
    assert nc(',') == ''
    assert nc(';') == ''
    assert nc(',;19-56;.,') == ''
    assert '1979' not in nc('Albert 1979')
    assert nc('Michael Ende') == nc('Ende, Michael')
    assert nc('Michael Ende') == nc('Ende, M.')
    assert nc('Michael Ende') == nc('M.Ende')
    assert nc('Michael Ende') == nc('M. Éndé, 1999')

    multi1 = nc('Frank Farian; Michael Ende')
    multi2 = nc('M.Ende; Farian, Frank')
    assert multi1 == multi2


def test_trim():
    text = 'ABC' * 200
    trimmed = meta.trim(text)[0]
    assert len(trimmed) == 128

    text = 'Iñtërnâtiônàlizætiøn☃💩'
    raw_len = len(text)
    trimmed = meta.trim(text)[0]
    assert raw_len == len(trimmed)


def test_sliding_window():

    assert meta.sliding_window('', width=4) == ['']
    assert meta.sliding_window('A', width=4) == ['A']
    assert meta.sliding_window('Hello', width=4) == ['Hell', 'ello']


def test_simhash():

    all_zero = 0b0.to_bytes(8, 'big')
    assert meta.simhash((all_zero, all_zero)) == all_zero

    all_ones = 0b11111111.to_bytes(1, 'big')
    assert meta.simhash((all_ones, all_ones)) == all_ones

    a = 0b0110.to_bytes(1, 'big')
    b = 0b1100.to_bytes(1, 'big')
    r = 0b1110.to_bytes(1, 'big')
    assert meta.simhash((a, b)) == r

    a = 0b01101001.to_bytes(1, 'big')
    b = 0b00111000.to_bytes(1, 'big')
    c = 0b11100100.to_bytes(1, 'big')
    r = 0b01101000.to_bytes(1, 'big')
    assert meta.simhash((a, b, c)) == r

    a = 0b0110100101101001.to_bytes(2, 'big')
    b = 0b0011100000111000.to_bytes(2, 'big')
    c = 0b1110010011100100.to_bytes(2, 'big')
    r = 0b0110100001101000.to_bytes(2, 'big')
    assert meta.simhash((a, b, c)) == r


def test_c2d():
    assert meta.c2d('AB6YHLNQIJYIM') == b'\x00}\x83\xad\xb0Bp\x86'


def test_c2i():
    assert meta.c2i('AB6YHLNQIJYIM') == 35329154098557062


def test_hamming_distance():
    a = 0b0001111
    b = 0b1000111
    assert meta.hamming_distance(a, b) == 2

    mid1 = meta.c2i(meta.generate_meta_id('Die Unendliche Geschichte', 'Michael Ende'))

    # Change one Character
    mid2 = meta.c2i(meta.generate_meta_id('Die UnXndliche Geschichte', 'Michael Ende'))
    assert meta.hamming_distance(mid1, mid2) <= 5

    # Delete one Character
    mid2 = meta.c2i(meta.generate_meta_id('Die nendliche Geschichte', 'Michael Ende'))
    assert meta.hamming_distance(mid1, mid2) <= 5

    # Add one Character
    mid2 = meta.c2i(meta.generate_meta_id('Die UnendlicheX Geschichte', 'Michael Ende'))
    assert meta.hamming_distance(mid1, mid2) <= 5

    # Add, change, delete
    mid2 = meta.c2i(meta.generate_meta_id('Diex Unandlische Geschiche', 'Michael Ende'))
    assert meta.hamming_distance(mid1, mid2) <= 8

    # Change Word order
    mid2 = meta.c2i(meta.generate_meta_id('Unendliche Geschichte, Die', 'Michael Ende'))
    assert meta.hamming_distance(mid1, mid2) <= 5

    # Totaly different
    mid2 = meta.c2i(meta.generate_meta_id('Now for something different'))
    assert meta.hamming_distance(mid1, mid2) >= 30


def test_jaccard():
    assert meta.jaccard_similarity(1, 2) == 0

