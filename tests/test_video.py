# -*- coding: utf-8 -*-
import pytest
from scenedetect import FrameTimecode
from iscc.core import code_video
from iscc import video, mp7
from blake3 import blake3
from tests import HERE
from os.path import join
from tests.test_readables import video_readables
from iscc_samples import videos
from iscc.schema import Uri

SAMPLE = join(HERE, "test.3gp")


def test_extract_video_metadata_readables():
    for readable in video_readables():
        meta = video.extract_video_metadata(readable)
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


def test_extract_video_preview_all_formats():
    result = video.extract_video_preview(videos()[2].as_posix())
    assert len(result) > 10


def test_extract_video_preview_readables():
    for r in video_readables():
        if isinstance(r, Uri.__args__) or hasattr(r, "name"):
            result = video.extract_video_preview(r)
            assert result[:10].hex() == "89504e470d0a1a0a0000"


def test_hash_video_0_features():
    assert video.hash_video([tuple([0] * 380)]) == b"\x00\x00\x00\x00\x00\x00\x00\x00"


def test_code_video():
    result = code_video(SAMPLE)
    assert "code" in result
    # assert "signature" in result
    # assert "crop" in result
    assert result["code"] == "EMAVMHMC7RMJF6XZ"
    # assert result["crop"] == "176:96:0:24"


def test_code_video_no_crop():
    result = code_video(SAMPLE, video_crop=False)
    assert result["code"] == "EMAV4DUC6QORW4X4"
    # assert "signature" in result
    assert "crop" not in result


def test_code_video_no_granular_no_preview():
    result = code_video(
        SAMPLE,
        video_granular=False,
        video_preview=False,
    )

    assert result == {
        "code": "EMAVMHMC7RMJF6XZ",
        "duration": 60.042,
        "fps": 24.0,
        "height": 144,
        "language": "en",
        "title": "Kali by Anokato - Spiral Sessions 2019",
        "width": 176,
    }


def test_code_video_granular_scenes():
    result = code_video(
        SAMPLE,
        video_granular=True,
        video_scenes=True,
        video_scenes_fs=0,
        video_scenes_th=50,
        video_scenes_min=15,
        video_scenes_ffmpeg=False,
        video_preview=False,
    )
    assert result == {
        "code": "EMAVMHMC7RMJF6XZ",
        "duration": 60.042,
        "features": {
            "features": [
                "DhuCPB1advw",
                "OgmyIIqHmiU",
                "Vo5C1g8Yvu0",
                "Zh2A_g9Sumg",
                "V56AtcCOpn8",
                "lJgzovjPltM",
                "Hp4D_XrSdtk",
                "Qpkisa6nWlM",
                "Vi2i7PwrGvM",
            ],
            "kind": "video",
            "sizes": [7.625, 2.5, 5.083, 1.25, 3.75, 2.792, 15.458, 8.167, 13.042],
            "version": 0,
        },
        "fps": 24.0,
        "height": 144,
        "language": "en",
        "title": "Kali by Anokato - Spiral Sessions 2019",
        "width": 176,
    }


def test_code_video_granular_scenes_ffmpeg():
    result = code_video(
        SAMPLE,
        video_granular=True,
        video_scenes=True,
        video_scenes_ffmpeg=True,
        video_scenes_ffmpeg_th=0.25,
        video_preview=False,
    )
    assert result == {
        "code": "EMAVMHMC7RMJF6XZ",
        "duration": 60.042,
        "features": {
            "features": [
                "DhuCPB1advw",
                "OgmyIIqHmiU",
                "Vo5C1g8Yvu0",
                "Xp6D_XjS9tk",
                "SiAyoIw8cqg",
                "Apki-a7jWlM",
            ],
            "kind": "video",
            "sizes": [7.625, 2.5, 5.083, 23.25, 1.5, 6.667],
            "version": 0,
        },
        "fps": 24.0,
        "height": 144,
        "language": "en",
        "title": "Kali by Anokato - Spiral Sessions 2019",
        "width": 176,
    }


def test_code_video_granular_rolling():
    result = code_video(
        SAMPLE, video_granular=True, video_scenes=False, video_preview=False
    )
    assert result == {
        "code": "EMAVMHMC7RMJF6XZ",
        "duration": 60.042,
        "features": {
            "features": [
                "ThqCHh1advw",
                "Hg8iCIganm0",
                "Ug5Slg8Yvm0",
                "Vh-A9AXavm0",
                "Vpqj59COtlM",
                "HpoD93jC8FE",
                "Xp8D_fjS_NE",
                "XhcDvfjSXto",
                "XBiCvX4Ydvg",
                "Qhgi8c43UlE",
                "Qpki_fyjmHM",
                "Vi2iDFg7GoM",
                "Fo2ibLyjGVM",
            ],
            "kind": "video",
            "overlap": 3,
            "window": 7,
        },
        "fps": 24.0,
        "height": 144,
        "language": "en",
        "title": "Kali by Anokato - Spiral Sessions 2019",
        "width": 176,
    }


def test_code_video_include_mp7sig():
    result = code_video(SAMPLE, video_include_fingerprint=True)
    assert result["fingerprint"].endswith("SZVP2HM")


def test_code_video_preview():
    result = code_video(SAMPLE, video_preview=True)
    preview = result["preview"]
    assert preview.startswith("data:image/webp;base64,UklGRpoCAABXRUJQVlA4II4CAACQDQCd")
    assert preview.endswith("GvkEq8A/EtLg6gfFTFgDZr++JWCKAbvgD3Qmv6NBCua61VsXvvDGIAAA=")


def test_hash_video():
    features = [tuple(range(380))]
    assert video.hash_video(features, video_bits=64).hex() == "528f91431f7c4ad2"
    extended = video.hash_video(features, video_bits=256).hex()
    assert extended.startswith("528f91431f7c4ad2")


def test_compute_video_features_rolling():
    signature = video.extract_video_signature(SAMPLE)
    frames = mp7.read_ffmpeg_signature(signature)
    rolling_sigs = video.compute_video_features_rolling(frames)
    assert rolling_sigs == {
        "features": [
            "XxqD9x1a8nw",
            "Hg7Wdg0a8u0",
            "Vg6Q8A0e8uw",
            "Vg6E_AUU8uw",
            "fhqH3HUQ9vU",
            "XgoH9nVacvE",
            "XgwX9N1Sc3g",
            "Hi4X9P1acng",
            "H2qRtdwbcvk",
            "XEoAl8YVcqU",
            "Xk4A3dQVUqQ",
            "U06SYFUdUqs",
            "P06CXFQVUrU",
        ],
        "kind": "video",
        "overlap": 3,
        "window": 7,
    }


def test_compute_video_features_scenes():
    signature = video.extract_video_signature(SAMPLE, video_fps=5, video_hwaccel=None)
    frames = mp7.read_ffmpeg_signature(signature)
    scenes = video.detect_video_scenes(
        SAMPLE,
        video_scenes_fs=0,
        video_scenes_th=50,
        video_scenes_min=15,
    )
    scene_signatures = video.compute_video_features_scenes(frames, scenes)
    assert scene_signatures == {
        "features": [
            "XxqT9x1a8vw",
            "HEqSSwAW8oQ",
            "VA7Q9A0esuw",
            "VgYGfAjUsmQ",
            "dw6FTHUE4nU",
            "vBqD3XVSdtE",
            "Hg4X9f1acvg",
            "XkoAn4YVcqU",
            "V06CXBQdUrU",
        ],
        "kind": "video",
        "sizes": [7.625, 2.5, 5.083, 1.25, 3.75, 2.792, 15.458, 8.167, 13.042],
        "version": 0,
    }


def test_extract_video_signature_readables():
    for readable in video_readables():
        if isinstance(readable, Uri.__args__) or hasattr(readable, "name"):
            result = video.extract_video_signature(readable)
            assert result[:10].hex() == "00000001800000000057"
        else:
            with pytest.raises(ValueError):
                video.extract_video_signature(readable)


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


def test_detect_video_scenes_pyscene():
    assert (
        video.detect_video_scenes(
            SAMPLE,
            video_scenes_fs=0,
            video_scenes_th=50,
            video_scenes_min=15,
        )
        == [7.625, 10.125, 15.208, 16.458, 20.208, 23.0, 38.458, 46.625, 59.667, 60.042]
    )


def test_detect_video_scenes_ffmpeg():
    _, scenes = video.extract_video_signature_cutpoints(
        SAMPLE, video_scenes_ffmpeg_th=0.24
    )
    assert scenes == [7.625, 10.125, 15.208, 30.875, 36.0, 38.458, 39.958, 46.625, 60.0]
