# -*- coding: utf-8 -*-
import subprocess
from pathlib import Path
from tempfile import gettempdir, mkdtemp

from loguru import logger as log
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


FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
WINDOW = 7
OVERLAP = 3
Scene = Tuple[FrameTimecode, FrameTimecode]
SceneSig = Tuple[float, str]


def compute_video_hash(features, bits=64):
    # type: (Sequence[Tuple[int]], int) -> bytes
    """Compute wta-hash for a list of frame signature vectors"""
    sigs = set(features)
    vecsum = [sum(col) for col in zip(*sigs)]
    video_hash = wtahash(vecsum, hl=bits)
    return video_hash


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


def compute_scene_signatures(frames, scenes):
    # type: (List[Frame], List[Scene]) -> List[SceneSig]
    """Compute video signatures for individuale scenes in video."""
    scenes_fc = scenes[-1][-1].get_frames()
    frames_fc = len(frames)
    assert scenes_fc == frames_fc, f"{scenes_fc} scenes vs {frames_fc} frames"
    result = []
    for start, end in scenes:
        scene_duration = end.get_seconds() - start.get_seconds()
        scene_duration = round(scene_duration, 3)
        scene_frames = frames[start.get_frames() : end.get_frames()]
        scene_sigs = [tuple(frame.vector.tolist()) for frame in scene_frames]
        scene_hash = compute_video_hash(scene_sigs)
        result.append((scene_duration, encode_base64(scene_hash)))
    return result


def compute_rolling_signatures(frames, window=WINDOW, overlap=OVERLAP):
    # type: (List[Frame], int, int) -> List[str]
    """
    Compute video signatures based on rolling window.

    Generates segment-wise features where 'window' is the duration of segments in
    seconds and 'overlap' is the number of seconds that overlap for each segment.
    """
    pass
