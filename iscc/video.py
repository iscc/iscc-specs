# -*- coding: utf-8 -*-
import subprocess
from pathlib import Path
from tempfile import mkdtemp
import os
import sys
from subprocess import Popen, PIPE, DEVNULL
from os.path import basename, dirname
from secrets import token_hex
from typing import Generator, List, Sequence, Tuple, Optional
import imageio_ffmpeg
from statistics import mode
from scenedetect import ContentDetector, FrameTimecode, SceneManager, VideoManager
from iscc.codec import encode_base64
from iscc.utils import cd
from iscc.wtahash import wtahash
from iscc.mp7 import Frame
import av


FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
WINDOW = 7  # Default window size in seconds
OVERLAP = 3  # Default overlap size in seconds
Scene = Tuple[FrameTimecode, FrameTimecode]
SceneSig = Tuple[List[str], List[int]]  # feature hashes, scene durations


def compute_video_hash(features, bits=64):
    # type: (Sequence[Tuple[int]], int) -> bytes
    """Compute wta-hash for a list of frame signature vectors"""
    sigs = set(features)
    vecsum = [sum(col) for col in zip(*sigs)]
    video_hash = wtahash(vecsum, hl=bits)
    return video_hash


def compute_rolling_signatures(frames, window=WINDOW, overlap=OVERLAP):
    # type: (List[Frame], int, int) -> List[str]
    """
    Compute video signatures based on rolling window.

    Generates segment-wise features where 'window' is the duration of segments in
    seconds and 'overlap' is the number of seconds that overlap for each segment.
    """
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
                sigs.append(encode_base64(compute_video_hash(segment_frames)))
                break
    return sigs


def compute_scene_signatures(frames, scenes):
    # type: (List[Frame], List[Scene]) -> Tuple[List[str], List[float]]
    """Compute video signatures for individual scenes in video.
    Returns features and durations as tuple.
    """
    scenes_fc = scenes[-1][-1].get_frames()
    frames_fc = len(frames)
    assert scenes_fc == frames_fc, f"{scenes_fc} scenes vs {frames_fc} frames"
    durations, features = [], []
    for start, end in scenes:
        scene_duration = end.get_seconds() - start.get_seconds()
        scene_duration = round(scene_duration, 3)
        scene_frames = frames[start.get_frames() : end.get_frames()]
        scene_sigs = [tuple(frame.vector.tolist()) for frame in scene_frames]
        scene_hash = compute_video_hash(scene_sigs)
        durations.append(scene_duration)
        features.append(encode_base64(scene_hash))
    return features, durations


def extract_signature(file_path, crop=None):
    # type: (str, Optional[str]) -> bytes
    """Extracts MP7 Video Signature"""
    sigfile = basename(file_path) + ".bin"
    folder = dirname(file_path)
    if crop:
        vf = "{},signature=format=binary:filename={}".format(crop, sigfile)
    else:
        vf = "signature=format=binary:filename={}".format(sigfile)
    with cd(folder):
        cmd = [FFMPEG, "-i", file_path, "-vf", vf, "-f", "null", "-"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(sigfile, "rb") as infile:
            sigdata = infile.read()
        os.remove(sigfile)
    return sigdata


def signature_extractor(crop=None):
    # type: (Optional[str]) -> Generator
    """Streaming signature generator (use gen.send(chunk))."""

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


def detect_crop(file_path):
    # type: (str) -> str
    """
    Detect crop value for video.
    Example result: crop=176:96:0:24
    """
    cmd = [FFMPEG, "-i", file_path, "-vf", "cropdetect", "-f", "null", "-"]
    res = subprocess.run(cmd, stderr=subprocess.PIPE)
    text = res.stderr.decode(encoding=sys.stdout.encoding)
    crops = [
        line.split()[-1]
        for line in text.splitlines()
        if line.startswith("[Parsed_cropdetect")
    ]
    return mode(crops)


def detect_scenes(video_file):
    # type: (str) -> List[Tuple[FrameTimecode, FrameTimecode]]
    """Compute Scenedetection and return cutpoints"""
    video_manager = VideoManager([video_file])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=50.0, min_scene_len=15))
    base_timecode = video_manager.get_base_timecode()
    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager, show_progress=False)
    return scene_manager.get_scene_list(base_timecode)


def get_metadata(video):
    with av.open(video) as container:
        duration = round(container.duration / 1000000, ndigits=3)
        format_ = container.format.long_name
        width = container.streams.video[0].format.width
        height = container.streams.video[0].format.height
        fps = container.streams.video[0].guessed_rate
        bitrate = container.bit_rate

        lang = set()
        for stream in container.streams:
            lang.add(stream.language)

        metadata = dict(
            duration=duration,
            format=format_,
            width=width,
            height=height,
            fps=round(float(fps), ndigits=3),
            bitrate=bitrate,
            language=lang.pop() if len(lang) == 1 else list(lang),
        )
        metadata.update(container.metadata)
        return dict(sorted(metadata.items()))
