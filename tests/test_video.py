# -*- coding: utf-8 -*-
import pytest
from scenedetect import FrameTimecode
from iscc.core import code_video
from iscc import video, mp7
from blake3 import blake3
from tests import HERE
from os.path import join


SAMPLE = join(HERE, "test.3gp")


def test_hach_video_0_features():
    with pytest.raises(AssertionError):
        video.hash_video([tuple([0] * 380)])


def test_code_video():
    result = code_video(SAMPLE)
    assert "code" in result
    # assert "signature" in result
    assert "crop" in result
    assert result["code"] == "EMAVMHMC7RMJF6XZ"
    assert result["crop"] == "176:96:0:24"


def test_code_video_no_crop():
    result = code_video(SAMPLE, video_crop=False)
    assert result["code"] == "EMAV4DUC6QORW4X4"
    # assert "signature" in result
    assert "crop" not in result


def test_code_video_granular_scenes():
    result = code_video(SAMPLE, video_granular=True, video_scenes=True)
    assert result == {
        "code": "EMAVMHMC7RMJF6XZ",
        "crop": "176:96:0:24",
        "duration": 60.042,
        "features": [
            "DhuCPB1advw",
            "OgmyIcqHmyU",
            "Vo5C1g8Yvu0",
            "dh2g_g_Sumk",
            "V5-AvcCOpn8",
            "lJgzpvjPltM",
            "Hp4D_XrSdtk",
            "Qpkise6nWlM",
            "Vi2i7PwrGvM",
        ],
        "fps": 24.0,
        "height": 144,
        "language": "en",
        "signature_fps": 5,
        "sizes": [7.625, 2.5, 5.083, 1.25, 3.75, 2.792, 15.458, 8.167, 13.042],
        "title": "Kali by Anokato - Spiral Sessions 2019",
        "width": 176,
    }


def test_code_video_granular_rolling():
    result = code_video(SAMPLE, video_granular=True, video_scenes=False)
    assert result == {
        "code": "EMAVMHMC7RMJF6XZ",
        "crop": "176:96:0:24",
        "duration": 60.042,
        "features": [
            "ThqCHh1advw",
            "Hg8iCIgavm0",
            "Ug5ylg8Yvm0",
            "Vh-A9gXavm0",
            "Vp6j59COtlM",
            "HpoD_3jS8FE",
            "Xp8D_fjS_NE",
            "XhcDvfjSXto",
            "XBiCvX4Ydvg",
            "Qhgi8c43UtE",
            "Qpki_fyjmHM",
            "Vi2iDFg7GoM",
            "Fo2ibPyjGVM",
        ],
        "fps": 24.0,
        "height": 144,
        "language": "en",
        "overlap": 3,
        "signature_fps": 5,
        "title": "Kali by Anokato - Spiral Sessions 2019",
        "width": 176,
        "window": 7,
    }


def test_code_video_include_mp7sig():
    result = code_video(SAMPLE, video_include_mp7sig=True)
    assert result["mp7sig"].endswith("SZVP2HM")


def test_code_video_preview():
    result = code_video(SAMPLE, video_preview=True)
    assert result["preview"].endswith("Z4h6t54UOnUxIAA")


def test_hash_video():
    features = [tuple(range(380))]
    assert video.hash_video(features, video_bits=64).hex() == "528f91431f7c4ad2"
    extended = video.hash_video(features, video_bits=256).hex()
    assert extended.startswith("528f91431f7c4ad2")


def test_compute_video_features_rolling():
    signature = video.extract_video_signature(SAMPLE)
    frames = mp7.read_ffmpeg_signature(signature)
    rolling_sigs = video.compute_video_features_rolling(frames)
    assert rolling_sigs == [
        "XxqT9x1b8nw",
        "Hi7Wfg0a8u0",
        "Vg7U8A0e8uw",
        "Vg6E_AUU8uw",
        "fhqH3HUQ9vU",
        "XgoH93VacvE",
        "Xg4X9N1Sc3g",
        "Hi4X9P1acng",
        "H2qRtdwbcvk",
        "XGoAl8YVcqU",
        "Xk4A3dQVUqQ",
        "U06SYFUdUqs",
        "f06CXFQVUrU",
    ]


def test_compute_video_features_scenes():
    signature = video.extract_video_signature(
        SAMPLE, video_granular=True, video_scenes=True
    )
    frames = mp7.read_ffmpeg_signature(signature)
    scenes = video.detect_video_scenes(SAMPLE)
    scene_signatures = video.compute_video_features_scenes(frames, scenes)
    assert scene_signatures == (
        [
            "XxqT9x1a8vw",
            "HGqWS0AW8oQ",
            "Vg7U9A0esuw",
            "VgYGfgj2tmQ",
            "dw6FTHUE4nU",
            "vhqD3XVSdtE",
            "Hg4X9f1acvg",
            "XkoAn8YVcqU",
            "V06CXBQdUrU",
        ],
        [7.625, 2.5, 5.083, 1.25, 3.75, 2.792, 15.458, 8.167, 13.042],
    )


def test_extract_video_signature():
    sigh = blake3(
        video.extract_video_signature(SAMPLE, video_scenes=True, video_fps=5)
    ).hexdigest()
    assert sigh == "da170784ef9e47f4f74289c3b2ff842887eda7641b8c53d4ab698ae0de6d7b1c"
    sigh = blake3(
        video.extract_video_signature(SAMPLE, video_scenes=False, video_fps=5)
    ).hexdigest()
    assert sigh == "da170784ef9e47f4f74289c3b2ff842887eda7641b8c53d4ab698ae0de6d7b1c"
    sigh = blake3(video.extract_video_signature(SAMPLE, video_fps=0)).hexdigest()
    assert sigh == "021f4901f79bbb5c49edb0027103ec352f2bdb4feca53e6ce4f2f7d76c3dab5f"


def test_extract_video_signature_with_crop():
    crop = video.detect_video_crop(SAMPLE)
    sigh = blake3(video.extract_video_signature(SAMPLE, crop, video_fps=0)).hexdigest()
    assert sigh == "5dc1f30d13d798b062c2a47870364a9f5a6e2161bdd6e242e93eb5e6309bc4fa"


def test_code_video_hwaccel():
    ra = code_video(SAMPLE)
    rb = code_video(SAMPLE, video_hwaccel="auto")
    assert ra == rb


def test_signature_extractor():
    sig1 = blake3(video.extract_video_signature(SAMPLE, video_fps=0)).hexdigest()
    gen = video._signature_extractor()
    with open(SAMPLE, "rb") as infile:
        data = infile.read(4096)
        while data:
            gen.send(data)
            data = infile.read(4096)
    result = next(gen)
    sig2 = blake3(result).hexdigest()
    assert sig1 == sig2


def test_detect_video_crop():
    assert video.detect_video_crop(SAMPLE) == "crop=176:96:0:24"


def test_detect_video_scenes():
    assert video.detect_video_scenes(SAMPLE) == [
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


def test_extract_video_metadata():
    meta = video.extract_video_metadata(SAMPLE)
    assert meta == {
        "duration": 60.042,
        "fps": 24.0,
        "height": 144,
        "language": "en",
        "title": "Kali by Anokato - Spiral Sessions 2019",
        "width": 176,
    }


def test_extract_video_metadata_open_file():
    with open(SAMPLE, "rb") as infile:
        meta = video.extract_video_metadata(infile)
        assert infile.tell() == 65536
        assert meta == {
            "duration": 60.042,
            "fps": 24.0,
            "height": 144,
            "language": "en",
            "title": "Kali by Anokato - Spiral Sessions 2019",
            "width": 176,
        }
