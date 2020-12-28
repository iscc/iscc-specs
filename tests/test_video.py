# -*- coding: utf-8 -*-
import pytest
from iscc.core import content_id_video
from iscc import video
from blake3 import blake3
from tests import HERE
from os.path import join


SAMPLE = join(HERE, "test.3gp")


def test_detect_crop():
    assert video.detect_crop(SAMPLE) == "crop=176:96:0:24"


def test_compute_signature_without_crop():
    sigh = blake3(video.compute_signature(SAMPLE)).hexdigest()
    assert sigh == "021f4901f79bbb5c49edb0027103ec352f2bdb4feca53e6ce4f2f7d76c3dab5f"


def test_compute_signature_with_crop():
    crop = video.detect_crop(SAMPLE)
    sigh = blake3(video.compute_signature(SAMPLE, crop)).hexdigest()
    assert sigh == "5dc1f30d13d798b062c2a47870364a9f5a6e2161bdd6e242e93eb5e6309bc4fa"


def test_signature_generator():
    gen = video.signature_generator()
    with open(SAMPLE, "rb") as infile:
        data = infile.read(4096)
        while data:
            gen.send(data)
            data = infile.read(4096)
    result = next(gen)
    sigh = blake3(result).hexdigest()
    assert sigh == "021f4901f79bbb5c49edb0027103ec352f2bdb4feca53e6ce4f2f7d76c3dab5f"


def test_content_id_video():
    assert content_id_video([tuple(range(380))]) == "CTURv6NMw3oub"


def test_content_id_video_0_features():
    with pytest.raises(AssertionError):
        content_id_video([tuple([0] * 380)])
