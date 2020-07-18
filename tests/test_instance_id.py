# -*- coding: utf-8 -*-
import iscc


def test_instance_id_empty():
    iid, tail, size = iscc.instance_id(b"")
    assert iid == "CRWTH7TBxg6Qh"
    assert tail == "Fci9dzWk4tBUmB5mrQGog2g4XSWeaCNRo"
    assert size == 0


def test_instance_id_zero():
    iid, tail, size = iscc.instance_id(b"\00")
    assert iid == "CR8DnfUwet2i8"
    assert tail == "7yfnwijKs4yhp9H1ohsVwn6Twgc18fAk6"
    assert size == 1


def test_instance_id_even():
    zero_bytes_even = b"\x00" * 16
    iid, tail, size = iscc.instance_id(zero_bytes_even)
    assert iid == "CRfawXPpg9YBp"
    assert isinstance(tail, str)
    assert tail == "ZrmFgwsJob8e42xhRJaqTUhnCfYaCboWd"
    assert size == len(zero_bytes_even)


def test_instance_id_uneven():
    ff_bytes_uneven = b"\xff" * 17
    iid, tail, size = iscc.instance_id(ff_bytes_uneven)
    assert iid == "CRD4vp2iBonAV"
    assert tail == "2m5BB7r4iEbsikGfcgrVEqCKQqAVbR4X5"
    assert size == len(ff_bytes_uneven)


def test_instance_id_more_bytes():
    more_bytes = b"\xcc" * 66000
    iid, tail, size = iscc.instance_id(more_bytes)
    assert tail == "3b1AFYxfRDyAjAyPNMTxnnXteFe6QgZfi"
    assert iid == "CRBMtvBsphc8X"
    assert size == 66000
