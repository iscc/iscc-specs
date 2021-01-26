# -*- coding: utf-8 -*-
import pytest
from scenedetect import FrameTimecode
from iscc.core import content_id_video
from iscc import video, mp7
from blake3 import blake3
from tests import HERE
from os.path import join


SAMPLE = join(HERE, "test.3gp")


def test_content_id_video_0_features():
    with pytest.raises(AssertionError):
        video.compute_video_hash([tuple([0] * 380)])


def test_content_id_video():
    result = content_id_video(SAMPLE)
    assert "code_video" in result
    # assert "signature" in result
    assert "crop" in result
    assert result["code_video"] == "EMAVMHMC7RMJF6XZ"
    assert result["crop"] == "176:96:0:24"


def test_content_id_video_no_crop():
    result = content_id_video(SAMPLE, crop=False)
    assert "code_video" in result
    # assert "signature" in result
    assert "crop" not in result
    assert result["code_video"] == "EMAV4DUD6RORW4X4"


def test_content_id_video_scenes():
    result = content_id_video(SAMPLE, scenes=True)
    assert "features" in result
    assert "sizes" in result


def test_content_id_video_rolling():
    result = content_id_video(SAMPLE, window=10, overlap=4)
    assert "features" in result
    assert "sizes" not in result
    assert result["window"] == 10
    assert result["overlap"] == 4


def test_compute_video_hash():
    features = [tuple(range(380))]
    assert video.compute_video_hash(features, 64).hex() == "528f91431f7c4ad2"
    extended = video.compute_video_hash(features, 256).hex()
    assert extended.startswith("528f91431f7c4ad2")


def test_compute_rolling_signatures():
    signature = video.extract_signature(SAMPLE)
    frames = mp7.read_ffmpeg_signature(signature)
    rolling_sigs = video.compute_rolling_signatures(frames)
    assert rolling_sigs == [
        "XxqD_x1a8ng",
        "Hi7Wfg0a8v0",
        "VA7U8A0f8uw",
        "Vg6E_AUW8uw",
        "fh6H3HUU9vU",
        "XhoH13VacvE",
        "XgwV9t1Sc3g",
        "XiwX9P1ac3g",
        "Hm4R9fxacvg",
        "FTuQt9wRUqE",
        "XkoA3cYVUqU",
        "V06CXFQVUqY",
        "V06SVFwdUrc",
        "V06GXBQd0vQ",
    ]


def test_compute_scene_signatures():
    signature = video.extract_signature(SAMPLE)
    frames = mp7.read_ffmpeg_signature(signature)
    scenes = video.detect_scenes(SAMPLE)
    scene_signatures = video.compute_scene_signatures(frames, scenes)
    assert scene_signatures == (
        [
            "XxqD_x1a8vw",
            "HEqWY8AX9oQ",
            "VA7U9A0f8-w",
            "V5QEfpj-tlQ",
            "dm6ETGUEwmc",
            "vhqD3HFKdtE",
            "Hg4X9f1acng",
            "XkoAn8YVcqU",
            "V06CXFQdUrQ",
            "XBgT_nxD8tE",
        ],
        [7.625, 2.5, 5.083, 1.25, 3.75, 2.792, 15.458, 8.167, 13.042, 0.375],
    )


def test_extract_signature():
    sigh = blake3(video.extract_signature(SAMPLE)).hexdigest()
    assert sigh == "021f4901f79bbb5c49edb0027103ec352f2bdb4feca53e6ce4f2f7d76c3dab5f"


def test_compute_signature_with_crop():
    crop = video.detect_crop(SAMPLE)
    sigh = blake3(video.extract_signature(SAMPLE, crop)).hexdigest()
    assert sigh == "5dc1f30d13d798b062c2a47870364a9f5a6e2161bdd6e242e93eb5e6309bc4fa"


def test_signature_extractor():
    sig1 = blake3(video.extract_signature(SAMPLE)).hexdigest()
    gen = video.signature_extractor()
    with open(SAMPLE, "rb") as infile:
        data = infile.read(4096)
        while data:
            gen.send(data)
            data = infile.read(4096)
    result = next(gen)
    sig2 = blake3(result).hexdigest()
    assert sig1 == sig2


def test_detect_crop():
    assert video.detect_crop(SAMPLE) == "crop=176:96:0:24"


def test_detect_scenes():
    assert video.detect_scenes(SAMPLE) == [
        (
            FrameTimecode(timecode=0, fps=24.000000),
            FrameTimecode(timecode=183, fps=24.000000),
        ),
        (
            FrameTimecode(timecode=183, fps=24.000000),
            FrameTimecode(timecode=243, fps=24.000000),
        ),
        (
            FrameTimecode(timecode=243, fps=24.000000),
            FrameTimecode(timecode=365, fps=24.000000),
        ),
        (
            FrameTimecode(timecode=365, fps=24.000000),
            FrameTimecode(timecode=395, fps=24.000000),
        ),
        (
            FrameTimecode(timecode=395, fps=24.000000),
            FrameTimecode(timecode=485, fps=24.000000),
        ),
        (
            FrameTimecode(timecode=485, fps=24.000000),
            FrameTimecode(timecode=552, fps=24.000000),
        ),
        (
            FrameTimecode(timecode=552, fps=24.000000),
            FrameTimecode(timecode=923, fps=24.000000),
        ),
        (
            FrameTimecode(timecode=923, fps=24.000000),
            FrameTimecode(timecode=1119, fps=24.000000),
        ),
        (
            FrameTimecode(timecode=1119, fps=24.000000),
            FrameTimecode(timecode=1432, fps=24.000000),
        ),
        (
            FrameTimecode(timecode=1432, fps=24.000000),
            FrameTimecode(timecode=1441, fps=24.000000),
        ),
    ]


def test_get_metadata():
    meta = video.get_metadata(SAMPLE)
    assert meta == {
        "duration": 60.042,
        "fps": 24.0,
        "height": 144,
        "language": "en",
        "title": "Kali by Anokato - Spiral Sessions 2019",
        "width": 176,
    }


def test_get_metadata_open_file():
    with open(SAMPLE, "rb") as infile:
        meta = video.get_metadata(infile)
        assert infile.tell() == 65536
        assert meta == {
            "duration": 60.042,
            "fps": 24.0,
            "height": 144,
            "language": "en",
            "title": "Kali by Anokato - Spiral Sessions 2019",
            "width": 176,
        }
