# -*- coding: utf-8 -*-
import pytest
from scenedetect import FrameTimecode

from iscc.core import content_id_video
from iscc import video, mp7
from blake3 import blake3
from tests import HERE
from os.path import join


SAMPLE = join(HERE, "test.3gp")


def test_detect_crop():
    assert video.detect_crop(SAMPLE) == "crop=176:96:0:24"


def test_compute_signature_without_crop():
    sigh = blake3(video.extract_signature(SAMPLE)).hexdigest()
    assert sigh == "021f4901f79bbb5c49edb0027103ec352f2bdb4feca53e6ce4f2f7d76c3dab5f"


def test_compute_signature_with_crop():
    crop = video.detect_crop(SAMPLE)
    sigh = blake3(video.extract_signature(SAMPLE, crop)).hexdigest()
    assert sigh == "5dc1f30d13d798b062c2a47870364a9f5a6e2161bdd6e242e93eb5e6309bc4fa"


def test_signature_generator():
    gen = video.signature_extractor()
    with open(SAMPLE, "rb") as infile:
        data = infile.read(4096)
        while data:
            gen.send(data)
            data = infile.read(4096)
    result = next(gen)
    sigh = blake3(result).hexdigest()
    assert sigh == "021f4901f79bbb5c49edb0027103ec352f2bdb4feca53e6ce4f2f7d76c3dab5f"


def test_compute_video_hash():
    assert video.compute_video_hash([tuple(range(380))]).hex() == "528f91431f7c4ad2"


def test_content_id_video_0_features():
    with pytest.raises(AssertionError):
        video.compute_video_hash([tuple([0] * 380)])


def test_content_id_video():
    assert content_id_video(SAMPLE) == "CTWkQX8PEkdCd"


def test_detect_scenes():
    assert video.detect_scenes(SAMPLE) == [
        (FrameTimecode(timecode=0, fps=24.000000),
         FrameTimecode(timecode=183, fps=24.000000)),
        (FrameTimecode(timecode=183, fps=24.000000),
         FrameTimecode(timecode=243, fps=24.000000)),
        (FrameTimecode(timecode=243, fps=24.000000),
         FrameTimecode(timecode=365, fps=24.000000)),
        (FrameTimecode(timecode=365, fps=24.000000),
         FrameTimecode(timecode=395, fps=24.000000)),
        (FrameTimecode(timecode=395, fps=24.000000),
         FrameTimecode(timecode=485, fps=24.000000)),
        (FrameTimecode(timecode=485, fps=24.000000),
         FrameTimecode(timecode=552, fps=24.000000)),
        (FrameTimecode(timecode=552, fps=24.000000),
         FrameTimecode(timecode=923, fps=24.000000)),
        (FrameTimecode(timecode=923, fps=24.000000),
         FrameTimecode(timecode=1119, fps=24.000000)),
        (FrameTimecode(timecode=1119, fps=24.000000),
         FrameTimecode(timecode=1432, fps=24.000000)),
        (FrameTimecode(timecode=1432, fps=24.000000),
         FrameTimecode(timecode=1441, fps=24.000000))
    ]


def test_compute_scene_signatures():
    signature = video.extract_signature(SAMPLE)
    frames = mp7.read_ffmpeg_signature(signature)
    scenes = video.detect_scenes(SAMPLE)
    scene_signatures = video.compute_scene_signatures(frames, scenes)
    assert scene_signatures == [
        (7.625, 'XxqD_x1a8vw'),
        (2.5, 'HEqWY8AX9oQ'),
        (5.083, 'VA7U9A0f8-w'),
        (1.25, 'V5QEfpj-tlQ'),
        (3.75, 'dm6ETGUEwmc'),
        (2.792, 'vhqD3HFKdtE'),
        (15.458, 'Hg4X9f1acng'),
        (8.167, 'XkoAn8YVcqU'),
        (13.042, 'V06CXFQdUrQ'),
        (0.375, 'XBgT_nxD8tE')
    ]
