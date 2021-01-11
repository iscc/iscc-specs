# -*- coding: utf-8 -*-
import pytest
from iscc import codec as c
from bitarray import bitarray as ba


def test_main_type():
    assert isinstance(c.MT.META, int)
    assert c.MT.META == 0
    assert c.MT.META.humanized == "meta-code"


def test_write_header():
    with pytest.raises(AssertionError):
        c.write_header(0, 0, 0, 0)
    assert c.write_header(0, 0, 0, 32) == bytes([0b0000_0000, 0b0000_0000])
    assert c.write_header(1, 0, 0, 32) == bytes([0b0001_0000, 0b0000_0000])
    assert c.write_header(7, 1, 1, 64) == bytes([0b0111_0001, 0b0001_0001])
    assert c.write_header(8, 1, 1, 64) == bytes([0b1000_0000, 0b0001_0001, 0b0001_0000])
    assert c.write_header(8, 8, 1, 64) == bytes([0b1000_0000, 0b1000_0000, 0b0001_0001])


def test_read_header():
    rh = c.read_header
    assert rh(bytes([0b0000_0000, 0b0000_0000])) == (0, 0, 0, 32, b"")
    assert rh(bytes([0b0000_0000, 0b0000_0000, 0b0000_0000])) == (0, 0, 0, 32, b"\x00")
    assert rh(bytes([0b0001_0000, 0b0000_0000])) == (1, 0, 0, 32, b"")
    assert rh(bytes([0b0111_0001, 0b0001_0001])) == (7, 1, 1, 64, b"")
    assert rh(bytes([0b1000_0000, 0b0001_0001, 0b0001_0000])) == (8, 1, 1, 64, b"")
    assert rh(bytes([0b1000_0000, 0b1000_0000, 0b0001_0001])) == (8, 8, 1, 64, b"")


def test_encode_base32():
    assert c.encode_base32(b"") == ""
    assert c.encode_base32(b"f") == "MY"
    assert c.encode_base32(b"fo") == "MZXQ"
    assert c.encode_base32(b"foo") == "MZXW6"
    assert c.encode_base32(b"foob") == "MZXW6YQ"
    assert c.encode_base32(b"fooba") == "MZXW6YTB"
    assert c.encode_base32(b"foobar") == "MZXW6YTBOI"


def test_decode_base32():
    assert c.decode_base32("") == b""
    assert c.decode_base32("MY") == b"f"
    assert c.decode_base32("My") == b"f"
    assert c.decode_base32("my") == b"f"
    assert c.decode_base32("MZXQ") == b"fo"
    assert c.decode_base32("MZXW6") == b"foo"
    assert c.decode_base32("MZXW6YQ") == b"foob"
    assert c.decode_base32("MZXW6YTB") == b"fooba"
    assert c.decode_base32("MZXW6YTBOI") == b"foobar"


def test_encode_base64():
    assert c.encode_base64(b"") == ""
    assert c.encode_base64(b"f") == "Zg"
    assert c.encode_base64(b"fo") == "Zm8"
    assert c.encode_base64(b"foo") == "Zm9v"
    assert c.encode_base64(b"foob") == "Zm9vYg"
    assert c.encode_base64(b"fooba") == "Zm9vYmE"
    assert c.encode_base64(b"foobar") == "Zm9vYmFy"


def test_decode_base64():
    assert c.decode_base64("") == b""
    assert c.decode_base64("Zg") == b"f"
    assert c.decode_base64("Zm8") == b"fo"
    assert c.decode_base64("Zm9v") == b"foo"
    assert c.decode_base64("Zm9vYg") == b"foob"
    assert c.decode_base64("Zm9vYmE") == b"fooba"
    assert c.decode_base64("Zm9vYmFy") == b"foobar"


def test_write_varnibble():
    with pytest.raises(ValueError):
        c._write_varnibble(-1)
    assert c._write_varnibble(0) == ba("0000")
    assert c._write_varnibble(7) == ba("0111")
    assert c._write_varnibble(8) == ba("10000000")
    assert c._write_varnibble(9) == ba("10000001")
    assert c._write_varnibble(71) == ba("10111111")
    assert c._write_varnibble(72) == ba("110000000000")
    assert c._write_varnibble(73) == ba("110000000001")
    assert c._write_varnibble(583) == ba("110111111111")
    assert c._write_varnibble(584) == ba("1110000000000000")
    assert c._write_varnibble(4679) == ba("1110111111111111")
    with pytest.raises(ValueError):
        c._write_varnibble(4680)
    with pytest.raises(TypeError):
        c._write_varnibble(1.0)


def test_read_varnibble():
    with pytest.raises(ValueError):
        c._read_varnibble(ba("0"))
    with pytest.raises(ValueError):
        c._read_varnibble(ba("1"))
    with pytest.raises(ValueError):
        c._read_varnibble(ba("011"))
    with pytest.raises(ValueError):
        c._read_varnibble(ba("100"))
    assert c._read_varnibble(ba("0000")) == (0, ba())
    assert c._read_varnibble(ba("000000")) == (0, ba("00"))
    assert c._read_varnibble(ba("0111")) == (7, ba())
    assert c._read_varnibble(ba("01110")) == (7, ba("0"))
    assert c._read_varnibble(ba("01111")) == (7, ba("1"))
    assert c._read_varnibble(ba("10000000")) == (8, ba())
    assert c._read_varnibble(ba("10000001")) == (9, ba())
    assert c._read_varnibble(ba("10000001110")) == (9, ba("110"))
    assert c._read_varnibble(ba("10111111")) == (71, ba())
    assert c._read_varnibble(ba("101111110")) == (71, ba("0"))
    assert c._read_varnibble(ba("110000000000")) == (72, ba())
    assert c._read_varnibble(ba("11000000000010")) == (72, ba("10"))
    assert c._read_varnibble(ba("110000000001")) == (73, ba())
    assert c._read_varnibble(ba("110000000001010")) == (73, ba("010"))
    assert c._read_varnibble(ba("110111111111")) == (583, ba())
    assert c._read_varnibble(ba("1101111111111010")) == (583, ba("1010"))
    assert c._read_varnibble(ba("1110000000000000")) == (584, ba())
    assert c._read_varnibble(ba("111000000000000001010")) == (584, ba("01010"))
    assert c._read_varnibble(ba("1110111111111111")) == (4679, ba())
    assert c._read_varnibble(ba("1110111111111111101010")) == (4679, ba("101010"))
