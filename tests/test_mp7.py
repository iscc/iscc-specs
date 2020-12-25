# -*- coding: utf-8 -*-
from lxml import etree
import numpy as np
from iscc.mp7 import read_ffmpeg_signature


def test_bin_integrety():
    signature_byte_data = open("ffmpeg_signature.bin", "rb").read()
    _ = read_ffmpeg_signature(signature_byte_data, test_mode=True)


def test_all_signatures():
    tree = etree.parse("ffmpeg_signature.xml")
    root = tree.getroot()
    z = root.getchildren()[0].getchildren()[0].getchildren()[0]
    l_xml = []
    for c in z.getchildren():
        if c.tag == "{urn:mpeg:mpeg7:schema:2001}VideoFrame":
            for cc in c.getchildren():
                if cc.tag == "{urn:mpeg:mpeg7:schema:2001}FrameSignature":
                    l_xml.append(
                        np.array([int(e) for e in cc.text.split("  ")], dtype=np.uint8)
                    )

    signature_byte_data = open("ffmpeg_signature.bin", "rb").read()
    l_bin = read_ffmpeg_signature(signature_byte_data)
    for xml, bin in zip(l_xml, l_bin):
        assert xml.all() == bin.vectors.all()
