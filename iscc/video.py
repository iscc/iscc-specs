# -*- coding: utf-8 -*-
from loguru import logger
import subprocess
from pathlib import Path
from tempfile import mkdtemp
import os
import sys
from subprocess import Popen, PIPE, DEVNULL
from secrets import token_hex
from typing import Any, Generator, List, Sequence, Tuple, Optional, Union
import imageio_ffmpeg
from statistics import mode
from langcodes import standardize_tag
from scenedetect import ContentDetector, FrameTimecode, SceneManager, VideoManager
from iscc import uread
from iscc.schema import FeatureType, Options, Readable, File, Uri
from iscc.codec import encode_base64
from iscc.wtahash import wtahash
from iscc.mp7 import Frame
import av


FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
Scene = Tuple[FrameTimecode, FrameTimecode]
SceneSig = Tuple[List[str], List[int]]  # feature hashes, scene durations


def extract_video_metadata(data):
    # type: (Union[Readable]) -> dict
    """Extract basic metadata from video files."""
    video = uread.open_data(data)
    with av.open(video) as v:
        metadata = {}
        c_duration = v.duration
        # Lower Case all keys in metadata
        c_metadata = {key.lower(): value for key, value in v.metadata.items()}
        vstreams = 0
        languages = set()
        metadata_fields = ["title"]
        for field in metadata_fields:
            value = c_metadata.get(field)
            if value:
                metadata[field] = value

        for stream in v.streams:
            if stream.type == "video":
                if vstreams == 0:
                    # Stream Duration
                    duration = stream.duration or c_duration
                    ds = round(float(duration * stream.time_base), ndigits=3)
                    if ds > 0:
                        metadata["duration"] = ds

                    fps = stream.guessed_rate
                    if fps:
                        metadata["fps"] = round(float(fps), ndigits=3)

                    # Stream Language
                    if stream.language and stream.language != "und":
                        languages.add(standardize_tag(stream.language))

                    # Stream Dimensions and FPS
                    format_attrs = ("width", "height")
                    for attr in format_attrs:
                        value = getattr(stream.format, attr)
                        if value:
                            metadata[attr] = value
                vstreams += 1
            if stream.type == "audio":
                # Add languages of audio streams
                if stream.language and stream.language != "und":
                    languages.add(standardize_tag(stream.language))
                if "duration" not in metadata:
                    # Stream Duration
                    duration = stream.duration or c_duration
                    ds = round(float(duration * stream.time_base), ndigits=3)
                    if ds > 0:
                        metadata["duration"] = ds

        lng = languages.pop() if len(languages) == 1 else list(languages)
        if lng:
            metadata["language"] = lng

        return dict(sorted(metadata.items()))


def extract_video_preview(file, **options):
    # type: (Union[File, Uri], **Any) -> Optional[bytes]
    """Extract thumbnail from video and return raw png byte data."""
    opts = Options(**options)
    size = opts.image_preview_size
    infile = uread.open_data(file)

    if not hasattr(infile, "name"):
        logger.warning("Cannot extract preview without file.name")
        return None

    file_path = infile.name

    cmd = [
        FFMPEG,
        "-i",
        file_path,
        "-vf",
        f"thumbnail,scale={size}:-1",
        "-frames:v",
        "1",
        "-c:v",
        "png",
        "-f",
        "image2pipe",
        "-",
    ]
    result = subprocess.run(cmd, stdout=PIPE, stderr=DEVNULL)
    return result.stdout


def extract_video_signature(uri, crop=None, **options):
    # type: (Union[File, Uri], Optional[str], **Any) -> bytes
    """Extract MPEG-7 Video Signature

    :param uri: File to process
    :param crop: FFMPEG style cropsting "w:h:x:y"
    :key video_fps: Frames per second for signature processing
    :key video_hwaccel: Hadware acceleration mode (None or "auto")
    :return: raw signature data
    """

    opts = Options(**options)

    infile = uread.open_data(uri)
    if not hasattr(infile, "name"):
        logger.error("Cannot extract signature without file.name")
        raise ValueError(f"Cannot extract signature from {type(infile)}")

    infile_path = infile.name
    sigfile_path = Path(mkdtemp(), token_hex(16) + ".bin")
    sigfile_path_escaped = sigfile_path.as_posix().replace(":", "\\\\:")

    vf = f"signature=format=binary:filename={sigfile_path_escaped}"
    if crop:
        vf = f"{crop}," + vf

    if opts.video_fps:
        vf = f"fps=fps={opts.video_fps}," + vf

    cmd = [FFMPEG]

    if opts.video_hwaccel is not None:
        cmd.extend(["-hwaccel", opts.video_hwaccel])

    cmd.extend(["-i", infile_path, "-vf", vf, "-f", "null", "-"])

    logger.debug(f"Extracting signature with {cmd}")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(sigfile_path, "rb") as sig:
        sigdata = sig.read()
    os.remove(sigfile_path)
    return sigdata


def hash_video(features, **options):
    # type: (Sequence[Tuple[int]], **int) -> bytes
    """Compute wta-hash for a list of frame signature vectors"""
    opts = Options(**options)
    sigs = set(features)
    vecsum = [sum(col) for col in zip(*sigs)]
    video_hash = wtahash(vecsum, hl=opts.video_bits)
    return video_hash


def compute_video_features_rolling(frames, **options):
    # type: (List[Frame], **int) -> dict
    """
    Compute video signatures based on rolling window.

    Generates segment-wise features where 'window' is the duration of segments in
    seconds and 'overlap' is the number of seconds that overlap for each segment.
    """
    opts = Options(**options)
    window = opts.video_window
    overlap = opts.video_overlap
    assert overlap < window, "Overlap must be shorter than window"
    shift = window - overlap
    cut_indexes = [0]
    start = 0
    for fidx, frame in enumerate(frames):
        if frame.elapsed > start + shift:
            cut_indexes.append(fidx)
            start = frame.elapsed
    sigs = []
    for ci in cut_indexes:
        segment_frames = []
        start = frames[ci].elapsed
        for frame in frames[ci:]:
            segment_frames.append(tuple(frame.vector.tolist()))
            if frame.elapsed > start + window:
                sigs.append(encode_base64(hash_video(segment_frames)))
                break
    return dict(
        kind=FeatureType.video.value, features=sigs, window=window, overlap=overlap
    )


def compute_video_features_scenes(frames, scenes):
    # type: (List[Frame], List[Scene]) -> dict
    """Compute video signatures for individual scenes in video.
    Returns features and durations as tuple.
    """

    scene_idx = 0
    scene = scenes[scene_idx]
    durations, features = [], []
    segment = []
    for fidx, frame in enumerate(frames):
        frame_t = tuple(frame.vector.tolist())
        segment.append(frame_t)
        if frame.elapsed >= scene[1].get_seconds():
            features.append(encode_base64(hash_video(segment)))
            segment = []
            duration = scene[1].get_seconds() - scene[0].get_seconds()
            duration = round(duration, 3)
            durations.append(duration)
            scene_idx += 1
            try:
                scene = scenes[scene_idx]
            except IndexError:
                break

    return dict(kind=FeatureType.video.value, features=features, sizes=durations)


def detect_video_crop(uri):
    # type: (Union[Uri, File]) -> str
    """
    Detect crop value for video.
    Example result: crop=176:96:0:24
    """

    infile = uread.open_data(uri)
    if not hasattr(infile, "name"):
        raise ValueError(f"Cannot extract signature for {type(infile)}")
    file_path = infile.name

    cmd = [
        FFMPEG,
        "-t",
        "3:00",
        "-i",
        file_path,
        "-vf",
        "cropdetect",
        "-f",
        "null",
        "-",
    ]
    res = subprocess.run(cmd, stderr=subprocess.PIPE)
    text = res.stderr.decode(encoding=sys.stdout.encoding)
    crops = [
        line.split()[-1]
        for line in text.splitlines()
        if line.startswith("[Parsed_cropdetect")
    ]
    return mode(crops)


def detect_video_scenes(uri, **options):
    # type: (Union[Uri, File], **Any) -> List[Tuple[FrameTimecode, FrameTimecode]]
    """Compute Scenedetection and return cutpoints.

    :param uri: Video file to be processed (file path or object)
    :key video_scenes_th: Threshold for scene detection. Higher value -> less scenes.
    :key video_scenes_fs: Frame Skip, number of frames to skip per processing step.
    :key video_scenes_min: Minimum number of frames per scene.
    :key video_scenes_previews: Generate per scene preview thumbnails.
    :return: List of tuples with start end end FrameTimecode.
    """

    opts = Options(**options)

    infile = uread.open_data(uri)
    if not hasattr(infile, "name"):
        raise ValueError(f"Cannot extract signature for {type(infile)}")
    file_path = infile.name

    video_manager = VideoManager([file_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(
            threshold=opts.video_scenes_th,
            min_scene_len=opts.video_scenes_min,
        )
    )
    base_timecode = video_manager.get_base_timecode()
    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(
        frame_source=video_manager, show_progress=False, frame_skip=opts.video_scenes_fs
    )
    return scene_manager.get_scene_list(base_timecode)


def _signature_extractor(crop=None):
    # type: (Optional[str]) -> Generator
    """Streaming signature generator (use gen.send(chunk)).
    WARNING: Not up to date
    """

    def raw_generator(crop=None):
        # type: (Optional[str]) -> Generator
        sigfile = Path(mkdtemp(), token_hex(16) + ".bin")
        # We need to escape colon from windows drive letter prefixes
        # See: https://stackoverflow.com/a/28770642/51627
        sigfile_escaped = sigfile.as_posix().replace(":", "\\\\:")
        if crop:
            vf = "{},signature=format=binary:filename={}".format(crop, sigfile_escaped)
        else:
            vf = "signature=format=binary:filename={}".format(sigfile_escaped)
        cmd = [FFMPEG, "-i", "-", "-vf", vf, "-f", "null", "-"]
        proc = Popen(cmd, stdout=DEVNULL, stderr=DEVNULL, stdin=PIPE)
        data = yield
        while data:
            proc.stdin.write(data)
            data = yield
        proc.stdin.close()
        proc.wait()
        with open(sigfile, "rb") as infile:
            sigdata = infile.read()
        os.remove(sigfile)
        yield sigdata

    initialized_generator = raw_generator(crop)
    next(initialized_generator)
    return initialized_generator
