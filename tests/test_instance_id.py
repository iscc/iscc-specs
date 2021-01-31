# -*- coding: utf-8 -*-
import iscc


def test_instance_id_empty():
    iid, tail, size = iscc.code_instance(b"")
    assert iid == "IAA26E2JXH27TING"
    assert tail == "UBAE32RW3TEUTG6LEXE23QISW7GJVE6K4QPTEYQ"
    assert size == 0


def test_instance_id_zero():
    iid, tail, size = iscc.code_instance(b"\00")
    assert iid == "IAAS2OW637YRWYPR"
    assert tail == "JSEG4NNPUA3HG3ONQ6TU2J5VYFIQEJOQ6WJOEEY"
    assert size == 1


def test_instance_id_even():
    zero_bytes_even = b"\x00" * 16
    iid, tail, size = iscc.code_instance(zero_bytes_even)
    assert iid == "IAA6K4W77ARQI4AL"
    assert isinstance(tail, str)
    assert tail == "QVVFKWWDURKY2DPTMRVDOJ4BMUACOCUTYZVKYHQ"
    assert size == len(zero_bytes_even)


def test_instance_id_uneven():
    ff_bytes_uneven = b"\xff" * 17
    iid, tail, size = iscc.code_instance(ff_bytes_uneven)
    assert iid == "IAA37KWEEXC5NXLC"
    assert tail == "B63AFIT532UEDT2CMGCASREX6WOYQG7J3CYWAHA"
    assert size == len(ff_bytes_uneven)


def test_instance_id_more_bytes():
    more_bytes = b"\xcc" * 66000
    iid, tail, size = iscc.code_instance(more_bytes)
    assert tail == "DRT54NORFPVGYXTQWQSO3YKQFVKKQSHZGGNEYJY"
    assert iid == "IAAT4ST2A3XFM7AQ"
    assert size == 66000
