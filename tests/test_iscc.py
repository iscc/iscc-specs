# -*- coding: utf-8 -*-
from io import BytesIO

from PIL import Image, ImageFilter, ImageEnhance

from iscc import iscc

TEXT_A = u"""
    Their most significant and usefull property of similarity-preserving
    fingerprints gets lost in the fragmentation of individual, propietary and
    use case specific implementations. The real benefit lies in similarity
    preservation beyond your local data archive on a global scale accross
    vendors.
"""

TEXT_B = u"""
    The most significant and usefull property of similarity-preserving
    fingerprints gets lost in the fragmentation of individual, propietary and
    use case specific implementations. The real benefit lies in similarity
    preservation beyond your local data archive on a global scale accross
    vendors.
"""

TEXT_C = u"""
    A need for open standard fingerprinting. We don´t need the best
    Fingerprinting algorithm just an accessible and widely used one.
"""


def test_encode_component():
    digest = bytes.fromhex('f7d3a5b201dc92f7a7')
    code = iscc.encode_component(digest)
    assert code == '5GcQF7sC3iY2i'


def test_decode():
    code = '5GcQF7sC3iY2i'
    digest = iscc.decode_component(code)
    assert digest.hex() == 'f7d3a5b201dc92f7a7'


def test_generate_meta_id():

    mid1 = iscc.generate_meta_id('Die Unendliche Geschichte')
    assert len(mid1) == 13
    assert "11jm9wZFS2NxJ" == mid1

    mid2 = iscc.generate_meta_id(' Die unéndlíche,  Geschichte ')
    assert mid1 == mid2

    mid3 = iscc.generate_meta_id('Die Unentliche Geschichte')
    assert 13 == iscc.component_hamming_distance(mid1, mid3)

    mid4 = iscc.generate_meta_id('Geschichte, Die Unendliche')
    assert 10 == iscc.component_hamming_distance(mid1, mid4)


def test_generate_content_id_text():
    cid_t_np = iscc.generate_content_id_text('')
    assert len(cid_t_np) == 13
    assert "1HD1n7nMDZBjr" == cid_t_np
    cid_t_p = iscc.generate_content_id_text('', partial=True)
    assert "1JD1n7nMDZBjr" == cid_t_p
    assert 0 == iscc.component_hamming_distance(cid_t_p, cid_t_np)

    cid_t_a = iscc.generate_content_id_text(TEXT_A)
    cid_t_b = iscc.generate_content_id_text(TEXT_B)
    assert 1 == iscc.component_hamming_distance(cid_t_a, cid_t_b)


def test_normalize_text():

    text = 'Iñtërnâtiônàlizætiøn☃💩 is a ticky \u00A0 thing'
    normalized = iscc.normalize_text(text)
    assert normalized == 'internationalizætiøn☃💩 is a ticky thing'


def test_normalize_creators():
    nc = iscc.normalize_creators
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
    multibyte_2 = 'ü' * 128
    trimmed = iscc.trim(multibyte_2)
    assert 64 == len(trimmed)
    assert 128 == len(trimmed.encode('utf-8'))

    multibyte_3 = "驩" * 128
    trimmed = iscc.trim(multibyte_3)
    assert 42 == len(trimmed)
    assert 126 == len(trimmed.encode('utf-8'))

    mixed = 'Iñtërnâtiônàlizætiøn☃💩' * 6
    trimmed = iscc.trim(mixed)
    assert 85 == len(trimmed)
    assert 128 == len(trimmed.encode('utf-8'))


def test_sliding_window():

    assert iscc.sliding_window('', width=4) == ['']
    assert iscc.sliding_window('A', width=4) == ['A']
    assert iscc.sliding_window('Hello', width=4) == ['Hell', 'ello']


def test_similarity_hash():

    all_zero = 0b0.to_bytes(8, 'big')
    assert iscc.similarity_hash((all_zero, all_zero)) == all_zero

    all_ones = 0b11111111.to_bytes(1, 'big')
    assert iscc.similarity_hash((all_ones, all_ones)) == all_ones

    a = 0b0110.to_bytes(1, 'big')
    b = 0b1100.to_bytes(1, 'big')
    r = 0b1110.to_bytes(1, 'big')
    assert iscc.similarity_hash((a, b)) == r

    a = 0b01101001.to_bytes(1, 'big')
    b = 0b00111000.to_bytes(1, 'big')
    c = 0b11100100.to_bytes(1, 'big')
    r = 0b01101000.to_bytes(1, 'big')
    assert iscc.similarity_hash((a, b, c)) == r

    a = 0b0110100101101001.to_bytes(2, 'big')
    b = 0b0011100000111000.to_bytes(2, 'big')
    c = 0b1110010011100100.to_bytes(2, 'big')
    r = 0b0110100001101000.to_bytes(2, 'big')
    assert iscc.similarity_hash((a, b, c)) == r


def test_c2d():
    assert iscc.c2d('AB6YHLNQIJYIM') == b'\x00}\x83\xad\xb0Bp\x86'


def test_c2i():
    assert iscc.c2i('AB6YHLNQIJYIM') == 35329154098557062


def test_hamming_distance():
    a = 0b0001111
    b = 0b1000111
    assert iscc.hamming_distance(a, b) == 2

    mid1 = iscc.generate_meta_id('Die Unendliche Geschichte', 'von Michael Ende')

    # Change one Character
    mid2 = iscc.generate_meta_id('Die UnXndliche Geschichte', 'von Michael Ende')
    assert iscc.component_hamming_distance(mid1, mid2) <= 10

    # Delete one Character
    mid2 = iscc.generate_meta_id('Die nendliche Geschichte', 'von Michael Ende')
    assert iscc.component_hamming_distance(mid1, mid2) <= 14

    # Add one Character
    mid2 = iscc.generate_meta_id('Die UnendlicheX Geschichte', 'von Michael Ende')
    assert iscc.component_hamming_distance(mid1, mid2) <= 13

    # Add, change, delete
    mid2 = iscc.generate_meta_id('Diex Unandlische Geschiche', 'von Michael Ende')
    assert iscc.component_hamming_distance(mid1, mid2) <= 18

    # Change Word order
    mid2 = iscc.generate_meta_id('Unendliche Geschichte, Die', 'von Michael Ende')
    assert iscc.component_hamming_distance(mid1, mid2) <= 13

    # Totaly different
    mid2 = iscc.generate_meta_id('Now for something different')
    assert iscc.component_hamming_distance(mid1, mid2) >= 30


def test_generate_instance_id():
    zero_bytes_even = b'\x00' * 16
    iid = iscc.generate_instance_id(zero_bytes_even)
    assert iscc.c2d(iid)[0] == 48
    assert iid == 'GAWKP4EYOCOTO'

    ff_bytes_uneven = b'\xff' * 17
    iid = iscc.generate_instance_id(ff_bytes_uneven)
    assert iscc.c2d(iid)[0] == 48
    assert iid == 'GAQV3LN3WYTQO'


def test_data_chunks():
    with open('lenna.jpg', 'rb') as infile:
        chunks1 = list(iscc.data_chunks(infile))
        infile.seek(0)
        chunks2 = list(iscc.data_chunks(infile.read()))
    assert len(chunks1) == 112
    assert len(chunks1[0]) == 38
    assert len(chunks1[-1]) == 2840
    assert len(chunks2) == 112
    assert len(chunks2[0]) == 38
    assert len(chunks2[-1]) == 2840


def test_generate_content_id_image():
    cid_i = iscc.generate_content_id_image('lenna.jpg')
    assert len(cid_i) == 13
    assert cid_i == '1KSbKdDLGvf8g'

    data = BytesIO(open('lenna.jpg', 'rb').read())
    cid_i = iscc.generate_content_id_image(data, partial=True)
    assert len(cid_i) == 13
    assert cid_i == '1LSbKdDLGvf8g'

    img1 = Image.open('lenna.jpg')
    img2 = img1.filter(ImageFilter.GaussianBlur(10))
    img3 = ImageEnhance.Brightness(img1).enhance(1.4)
    img4 = ImageEnhance.Contrast(img1).enhance(1.2)

    cid1 = iscc.generate_content_id_image(img1)
    cid2 = iscc.generate_content_id_image(img2)
    cid3 = iscc.generate_content_id_image(img3)
    cid4 = iscc.generate_content_id_image(img4)

    assert iscc.component_hamming_distance(cid1, cid2) == 1
    assert iscc.component_hamming_distance(cid1, cid3) == 1
    assert iscc.component_hamming_distance(cid1, cid4) == 1
