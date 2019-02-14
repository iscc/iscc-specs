# -*- coding: utf-8 -*-
import json
import random
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance
import iscc

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


def test_test_data():
    with open('test_data.json', encoding='utf-8') as jfile:
        data = json.load(jfile)
        assert type(data) == dict
        for funcname, tests in data.items():
            for testname, testdata in tests.items():
                func = getattr(iscc, funcname)
                args = testdata['inputs']
                if funcname in ['data_chunks']:
                    testdata['outputs'] = [
                        bytes.fromhex(i.split(':')[1]) for i
                        in testdata['outputs']
                    ]
                    result = list(func(*args))
                else:
                    result = func(*args)
                expected = testdata['outputs']

                assert result == expected, "%s %s " % (funcname, args)


def test_meta_id():

    mid1, _, _ = iscc.meta_id('ISCC Content Identifiers')
    assert mid1 == 'CCDFPFc87MhdT'

    mid1, title, extra = iscc.meta_id('Die Unendliche Geschichte')
    assert mid1 == "CCAKevDpE1eEL"
    assert title == 'Die Unendliche Geschichte'
    assert extra == ''
    mid2 = iscc.meta_id(' Die unéndlíche,  Geschichte ')[0]
    assert mid1 == mid2

    mid3 = iscc.meta_id('Die Unentliche Geschichte')[0]
    assert 8 == iscc.distance(mid1, mid3)

    mid4 = iscc.meta_id('Geschichte, Die Unendliche')[0]
    assert 9 == iscc.distance(mid1, mid4)


def test_encode():
    digest = bytes.fromhex('f7d3a5b201dc92f7a7')
    code = iscc.encode(digest)
    assert code == '5GcvF7s13LK2L'


def test_decode():
    code = '5GcQF7sC3iY2i'
    digest = iscc.decode(code)
    assert digest.hex() == 'f7d6bd587d22a7cb6d'


def test_content_id_text():
    cid_t_np = iscc.content_id_text('')
    assert len(cid_t_np) == 13
    assert "CTiesaXaMqbbU" == cid_t_np
    cid_t_p = iscc.content_id_text('', partial=True)
    assert "CtiesaXaMqbbU" == cid_t_p
    assert 0 == iscc.distance(cid_t_p, cid_t_np)

    cid_t_a = iscc.content_id_text(TEXT_A)
    cid_t_b = iscc.content_id_text(TEXT_B)
    assert 1 == iscc.distance(cid_t_a, cid_t_b)


def test_text_normalize():

    text = 'Iñtërnâtiônàlizætiøn☃💩 is a ticky \u00A0 thing'
    normalized = iscc.text_normalize(text)
    assert normalized == 'internationalizætiøn☃💩 is a ticky thing'

    assert iscc.text_normalize(' ') == ''
    assert iscc.text_normalize('  Hello  World ? ') == 'hello world'


def test_trim_text():
    multibyte_2 = 'ü' * 128
    trimmed = iscc.text_trim(multibyte_2)
    assert 64 == len(trimmed)
    assert 128 == len(trimmed.encode('utf-8'))

    multibyte_3 = "驩" * 128
    trimmed = iscc.text_trim(multibyte_3)
    assert 42 == len(trimmed)
    assert 126 == len(trimmed.encode('utf-8'))

    mixed = 'Iñtërnâtiônàlizætiøn☃💩' * 6
    trimmed = iscc.text_trim(mixed)
    assert 85 == len(trimmed)
    assert 128 == len(trimmed.encode('utf-8'))


def test_sliding_window():
    assert list(iscc.sliding_window('', width=4)) == ['']
    assert list(iscc.sliding_window('A', width=4)) == ['A']
    assert list(iscc.sliding_window('Hello', width=4)) == ['Hell', 'ello']
    words = ('lorem', 'ipsum', 'dolor', 'sit', 'amet')
    assert list(iscc.sliding_window(words, 2))[0] == ('lorem', 'ipsum')


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


def test_hamming_distance():
    a = 0b0001111
    b = 0b1000111
    assert iscc.distance(a, b) == 2

    mid1 = iscc.meta_id('Die Unendliche Geschichte', 'von Michael Ende')[0]

    # Change one Character
    mid2 = iscc.meta_id('Die UnXndliche Geschichte', 'von Michael Ende')[0]
    assert iscc.distance(mid1, mid2) <= 10

    # Delete one Character
    mid2 = iscc.meta_id('Die nendliche Geschichte', 'von Michael Ende')[0]
    assert iscc.distance(mid1, mid2) <= 14

    # Add one Character
    mid2 = iscc.meta_id('Die UnendlicheX Geschichte', 'von Michael Ende')[0]
    assert iscc.distance(mid1, mid2) <= 13

    # Add, change, delete
    mid2 = iscc.meta_id('Diex Unandlische Geschiche', 'von Michael Ende')[0]
    assert iscc.distance(mid1, mid2) <= 22

    # Change Word order
    mid2 = iscc.meta_id('Unendliche Geschichte, Die', 'von Michael Ende')[0]
    assert iscc.distance(mid1, mid2) <= 13

    # Totaly different
    mid2 = iscc.meta_id('Now for something different')[0]
    assert iscc.distance(mid1, mid2) >= 25


def test_content_id_mixed():
    cid_t_1 = iscc.content_id_text('Some Text')
    cid_t_2 = iscc.content_id_text('Another Text')

    cid_m = iscc.content_id_mixed([cid_t_1])
    assert cid_m == "CM3oME4TtXogc"

    cid_m = iscc.content_id_mixed([cid_t_1, cid_t_2])
    assert cid_m == "CM3RQtGc98nXg"

    cid_i = iscc.content_id_image('lenna.jpg')
    cid_m = iscc.content_id_mixed([cid_t_1, cid_t_2, cid_i])
    assert cid_m == "CM3ovx7zUEy38"


def test_data_id():
    random.seed(1)
    data = bytearray([random.getrandbits(8) for _ in range(1000000)])  # 1 mb
    did_a = iscc.data_id(data)
    assert did_a == 'CDjPCoxV16Ppq'
    data.insert(500000, 1)
    data.insert(500001, 2)
    data.insert(500002, 3)
    did_b = iscc.data_id(data)
    assert did_b == did_b
    for x in range(100):  # insert 100 bytes random noise
        data.insert(random.randint(0, 1000000), random.randint(0, 255))
    did_c = iscc.data_id(data)
    assert iscc.distance(did_a, did_c) == 7


def test_instance_id():
    zero_bytes_even = b'\x00' * 16
    iid, h = iscc.instance_id(zero_bytes_even)
    assert iid == 'CR8UZLfpaCm1d'
    assert h == '2ca7f098709d37d6f6a1a7e0670f49734c735500894aab4dc14d2c13f042dddd'
    ff_bytes_uneven = b'\xff' * 17
    iid, h = iscc.instance_id(ff_bytes_uneven)
    assert iid == 'CR6Nh6fvCxHj9'
    assert h == '215dadbbb627072c15b2235b521db9896e74d7ef379fdafa731efa52a67d5b7d'
    more_bytes = b'\xcc' * 66000
    iid, h = iscc.instance_id(more_bytes)
    assert h == 'db5f55fc6741664fda4ebb364f2cad99f6ac166aedc7551ab0768c6c67218f71'
    assert iid == 'CRdhBqWwY7u7i'


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


def test_content_id_image():
    cid_i = iscc.content_id_image('lenna.jpg')
    assert len(cid_i) == 13
    assert cid_i == 'CYmLoqBRgV32u'

    data = BytesIO(open('lenna.jpg', 'rb').read())
    cid_i = iscc.content_id_image(data, partial=True)
    assert len(cid_i) == 13
    assert cid_i == 'CimLoqBRgV32u'

    img1 = Image.open('lenna.jpg')
    img2 = img1.filter(ImageFilter.GaussianBlur(10))
    img3 = ImageEnhance.Brightness(img1).enhance(1.4)
    img4 = ImageEnhance.Contrast(img1).enhance(1.2)

    cid1 = iscc.content_id_image(img1)
    cid2 = iscc.content_id_image(img2)
    cid3 = iscc.content_id_image(img3)
    cid4 = iscc.content_id_image(img4)

    assert iscc.distance(cid1, cid2) == 0
    assert iscc.distance(cid1, cid3) == 2
    assert iscc.distance(cid1, cid4) == 0


def test_pi():
    """Check that PI has expected value on system"""
    import math
    assert math.pi == 3.141592653589793
