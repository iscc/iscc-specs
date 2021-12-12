# -*- coding: utf-8 -*-
import json
from fractions import Fraction

from codetiming import Timer
from iscc_core.code_content_video import soft_hash_video_v0
from loguru import logger as log
import subprocess
from pathlib import Path
from tempfile import mkdtemp
import os
import sys
from subprocess import Popen, PIPE, DEVNULL
from secrets import token_hex
from typing import Any, Generator, List, Tuple, Optional, Union
from statistics import mode
from langcodes import standardize_tag
from iscc.options import SdkOptions
from iscc import uread
from iscc.schema import FeatureType, Readable, File, Uri
from iscc_core.codec import encode_base64
from iscc.mp7 import Frame
from iscc.bin import ffmpeg_bin, ffprobe_bin
import jmespath
import iscc_core


FFMPEG = ffmpeg_bin()
FFPROBE = ffprobe_bin()
Scene = Union[Tuple["FrameTimecode", "FrameTimecode"], Tuple[float, float]]
SceneSig = Tuple[List[str], List[int]]  # feature hashes, scene durations


def extract_video_metadata(file):
    # type: (Union[File, Uri]) -> dict

    infile = uread.open_data(file)
    if not hasattr(infile, "name"):
        log.warning("Cannot extract video metadata without file.name")
        return dict()
    file_path = infile.name

    cmd = [
        FFPROBE,
        "-hide_banner",
        "-loglevel",
        "fatal",
        "-find_stream_info",
        "-show_error",
        "-show_format",
        "-show_streams",
        "-show_programs",
        "-show_chapters",
        "-show_private_data",
        "-print_format",
        "json",
        "-i",
        file_path,
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    metadata = json.loads(res.stdout)

    video_streams = jmespath.search("streams[?codec_type=='video']", metadata)
    n_streams = len(video_streams)
    if n_streams == 0:
        raise ValueError("No video stream detected")
    if n_streams != 1:
        log.warning(f"Detected {n_streams} video streams.")

    vstream = video_streams[0]

    result = iscc_core.ContentCodeVideo(iscc="dummy")

    # Duration
    duration_format = [jmespath.search("format.duration", metadata)]
    duration_streams = jmespath.search(
        "streams[?codec_type=='video'].duration", metadata
    )
    durations = duration_format + duration_streams
    duration = max(round(float(d), 3) for d in durations)
    result.duration = duration

    # Dimensions
    result.height = vstream.get("height")
    result.width = vstream.get("width")

    # FPS
    fps = vstream.get("r_frame_rate")
    if fps:
        fps = round(float(Fraction(fps)), 3)
        result.fps = fps

    # Title
    result.title = jmespath.search("format.tags.title", metadata)

    # Language
    langs = jmespath.search("streams[*].tags.language", metadata)
    lang = jmespath.search("format.tags.language", metadata)
    if lang:
        langs.insert(0, lang)
    if langs:
        result.language = standardize_tag(langs[0])

    return result.dict(exclude={"iscc"})


def extract_video_preview(file, **options):
    # type: (Union[File, Uri], **Any) -> Optional[bytes]
    """Extract thumbnail from video and return raw png byte data."""
    opts = SdkOptions(**options)
    size = opts.image_preview_size
    infile = uread.open_data(file)

    if not hasattr(infile, "name"):
        log.warning("Cannot extract preview without file.name")
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
    with Timer(text="video preview extraction took {:0.4f}s", logger=log.debug):
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

    opts = SdkOptions(**options)

    infile = uread.open_data(uri)
    if not hasattr(infile, "name"):
        log.error("Cannot extract signature without file.name")
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

    log.debug(f"video sig extraction with {cmd}")
    with Timer(text="video sig extraction took {:0.4f}s", logger=log.debug):
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(sigfile_path, "rb") as sig:
        sigdata = sig.read()
    os.remove(sigfile_path)
    return sigdata


def extract_video_signature_cutpoints(uri, crop=None, **options):
    # type: (Union[File, Uri], Optional[str], **Any) -> Tuple[bytes, List[Scene]]
    """Extract MPEG-7 Video Signature together with ffmpeg scdet cutponts

    :param uri: File to process
    :param crop: FFMPEG style cropsting "w:h:x:y"
    :key video_fps: Frames per second for signature processing
    :key video_hwaccel: Hadware acceleration mode (None or "auto")
    :return: raw signature data
    """

    opts = SdkOptions(**options)

    infile = uread.open_data(uri)
    if not hasattr(infile, "name"):
        log.error("Cannot extract signature without file.name")
        raise ValueError(f"Cannot extract signature from {type(infile)}")

    infile_path = infile.name
    sig_path = Path(mkdtemp(), token_hex(16) + ".bin")
    sig_path_escaped = sig_path.as_posix().replace(":", "\\\\:")
    scene_path = Path(mkdtemp(), token_hex(16) + ".cut")
    scene_path_escaped = scene_path.as_posix().replace(":", "\\\\:")

    sig = f"signature=format=binary:filename={sig_path_escaped}"
    if crop:
        sig = f"{crop}," + sig

    if opts.video_fps:
        sig = f"fps=fps={opts.video_fps}," + sig

    scene = f"select='gte(scene,0)',metadata=print:file={scene_path_escaped}"

    cmd = [
        FFMPEG,
    ]

    if opts.video_hwaccel is not None:
        cmd.extend(["-hwaccel", opts.video_hwaccel])

    cmd.extend(
        [
            "-i",
            infile_path,
            "-an",
            "-sn",
            "-filter_complex",
            f"split[in1][in2];[in1]{scene}[out1];[in2]{sig}[out2]",
            "-map",
            "[out1]",
            "-f",
            "null",
            "-",
            "-map",
            "[out2]",
            "-f",
            "null",
            "-",
        ]
    )

    log.debug(f"video sig and cutpoint extraction with {subprocess.list2cmdline(cmd)}")
    with Timer(
        text="video sig and cutpoint extraction took {:0.3f}s", logger=log.debug
    ):
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(sig_path, "rb") as sigin:
        sigdata = sigin.read()
    with open(scene_path, "rt", encoding="utf-8") as scenein:
        scenetext = scenein.read()
    os.remove(sig_path)
    os.remove(scene_path)
    scenes = parse_ffmpeg_scenes(scenetext, **options)
    return sigdata, scenes


def compute_video_features_rolling(frames, **options):
    # type: (List[Frame], **int) -> dict
    """
    Compute video signatures based on rolling window.

    Generates segment-wise features where 'window' is the duration of segments in
    seconds and 'overlap' is the number of seconds that overlap for each segment.
    """
    opts = SdkOptions(**options)
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
                sigs.append(encode_base64(soft_hash_video_v0(segment_frames, bits=64)))
                break
    return dict(
        kind=FeatureType.video.value, features=sigs, window=window, overlap=overlap
    )


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
    # type: (Union[Uri, File], **Any) -> List[float]
    """Compute Scenedetection and return cutpoints.

    :param uri: Video file to be processed (file path or object)
    :key video_scenes_th: Threshold for scene detection. Higher value -> less scenes.
    :key video_scenes_fs: Frame Skip, number of frames to skip per processing step.
    :key video_scenes_min: Minimum number of frames per scene.
    :key video_scenes_previews: Generate per scene preview thumbnails.
    :return: List of tuples with start end end FrameTimecode.
    """
    try:
        from scenedetect import (
            ContentDetector,
            FrameTimecode,
            SceneManager,
            VideoManager,
        )
    except ImportError:
        raise EnvironmentError(
            "Please install `scenedetect`python module for advanced scenedetection."
        )

    opts = SdkOptions(**options)

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

    with Timer(text="video scene detection took {:0.4f}s", logger=log.debug):
        scene_manager.detect_scenes(
            frame_source=video_manager,
            show_progress=False,
            frame_skip=opts.video_scenes_fs,
        )
    # Use end frames from scene_list to exclude 0 and include last frame time
    scenes = scene_manager.get_scene_list(base_timecode)
    cutlist = [round(float(scene[1].get_seconds()), 3) for scene in scenes]
    return cutlist


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


def parse_ffmpeg_scenes(scene_text, **options):
    # type: (str, **Any) -> List[float]
    """Parse scene score output from ffmpeg

    :param str scene_text: Scene score output from ffmpeg
    :key float video_scenes_ffmpeg_th: Scene Score threshold for valid cutpoint
    """
    if not scene_text.strip():
        return []

    opts = SdkOptions(**options)
    times = []
    scores = []
    for line in scene_text.splitlines():
        if line.startswith("frame:"):
            ts = round(float(line.split()[-1].split(":")[-1]), 3)
            times.append(ts)
        if line.startswith("lavfi.scene_score"):
            scores.append(float(line.split("=")[-1]))

    cutpoints = []
    for ts, score in zip(times, scores):
        if score >= opts.video_scenes_ffmpeg_th:
            cutpoints.append(ts)

    # append last frame timestamp if not in cutpoints
    if cutpoints and cutpoints[-1] != times[-1]:
        cutpoints.append(times[-1])

    return cutpoints[1:]


def compute_video_features_scenes(frames, scenes):
    # type: (List[Frame], List[float]) -> dict
    """Compute video signatures for individual scenes in video.
    Returns a dictionary conforming to `shema.Feature`- objects.
    """
    features, sizes, segment = [], [], []
    start_frame = 0
    for cidx, cutpoint in enumerate(scenes):
        try:
            frames = frames[start_frame:]
        except IndexError:
            break
        for fidx, frame in enumerate(frames):
            frame_t = tuple(frame.vector.tolist())
            segment.append(frame_t)
            if frame.elapsed >= cutpoint:
                features.append(encode_base64(soft_hash_video_v0(segment, 64)))
                segment = []
                prev_cutpoint = 0 if cidx == 0 else scenes[cidx - 1]
                duration = round(cutpoint - prev_cutpoint, 3)
                sizes.append(duration)
                start_frame = fidx + 1
                break
    if not features:
        log.info("No scenes detected. Use all frames")
        segment = [tuple(frame.vector.tolist()) for frame in frames]
        features = [encode_base64(soft_hash_video_v0(segment, 64))]
        sizes = [round(float(frames[-1].elapsed), 3)]

    return dict(kind=FeatureType.video.value, version=0, features=features, sizes=sizes)


if __name__ == "__main__":
    from iscc_samples import videos
    from pprint import pprint

    r = extract_video_metadata2(videos()[1])
    pprint(r, sort_dicts=False)
