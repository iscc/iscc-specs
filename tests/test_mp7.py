# -*- coding: utf-8 -*-
from lxml import etree
import numpy as np
from iscc.mp7 import read_ffmpeg_signature
from fractions import Fraction

example_bin = "ffmpeg_signature.bin"
example_xml = "ffmpeg_signature.xml"


def test_bin_integrity():
    signature_byte_data = open(example_bin, "rb").read()
    _ = read_ffmpeg_signature(signature_byte_data, test_mode=True)


def test_all_signatures():
    tree = etree.parse(example_xml)
    root = tree.getroot()
    l_xml = []
    for c in root.getchildren()[0].getchildren()[0].getchildren()[0].getchildren():
        if c.tag == "{urn:mpeg:mpeg7:schema:2001}VideoFrame":
            for cc in c.getchildren():
                if cc.tag == "{urn:mpeg:mpeg7:schema:2001}FrameSignature":
                    l_xml.append(
                        np.array([int(e) for e in cc.text.split("  ")], dtype=np.uint8)
                    )

    signature_byte_data = open(example_bin, "rb").read()
    l_bin = read_ffmpeg_signature(signature_byte_data)
    last_elapsed = Fraction(0, 1)
    for xml, bin in zip(l_xml, l_bin):
        assert xml.all() == bin.vectors.all()
        assert 0 <= bin.confidence <= 256
        assert last_elapsed <= bin.elapsed
        last_elapsed = bin.elapsed
