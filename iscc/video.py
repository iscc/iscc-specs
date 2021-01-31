# -*- coding: utf-8 -*-
from loguru import logger
import subprocess
from pathlib import Path
from tempfile import mkdtemp
import os
import sys
from subprocess import Popen, PIPE, DEVNULL
from os.path import basename, dirname
from secrets import token_hex
from typing import Any, Generator, List, Sequence, Tuple, Optional, BinaryIO, Union
import imageio_ffmpeg
from statistics import mode
from langcodes import standardize_tag
from scenedetect import ContentDetector, FrameTimecode, SceneManager, VideoManager
from iscc.schema import Opts
from iscc.codec import encode_base64
from iscc.utils import cd
from iscc.wtahash import wtahash
from iscc.mp7 import Frame
import av


FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
Scene = Tuple[FrameTimecode, FrameTimecode]
SceneSig = Tuple[List[str], List[int]]  # feature hashes, scene durations


def hash_video(features, **kwargs):
    # type: (Sequence[Tuple[int]], **int) -> bytes
    """Compute wta-hash for a list of frame signature vectors"""
    opts = Opts(**kwargs)
    sigs = set(features)
    vecsum = [sum(col) for col in zip(*sigs)]
    video_hash = wtahash(vecsum, hl=opts.video_bits)
    return video_hash


def compute_rolling_signatures(frames, **kwargs):
    # type: (List[Frame], **int) -> List[str]
    """
    Compute video signatures based on rolling window.

    Generates segment-wise features where 'window' is the duration of segments in
    seconds and 'overlap' is the number of seconds that overlap for each segment.
    """
    opts = Opts(**kwargs)
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
    return sigs


def compute_scene_signatures(frames, scenes):
    # type: (List[Frame], List[Scene]) -> Tuple[List[str], List[float]]
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

    return features, durations


def extract_video_preview(file_path, **options):
    # type: (str, **Any) -> bytes
    """Extract thumbnail from video and return raw png byte data."""
    opts = Opts(**options)
    size = opts.image_preview_size
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


def extract_signature(file_path, crop=None, **kwargs):
    # type: (str, Optional[str], **Any) -> bytes
    """Extracts MP7 Video Signature"""
    opts = Opts(**kwargs)
    sigfile = basename(file_path) + ".bin"
    folder = dirname(file_path)

    vf = f"signature=format=binary:filename={sigfile}"
    if crop:
        vf = f"{crop}," + vf

    if opts.video_fps:
        vf = f"fps=fps={opts.video_fps}," + vf

    cmd = [FFMPEG]

    if opts.video_hwaccel is not None:
        cmd.extend(["-hwaccel", opts.video_hwaccel])

    cmd.extend(["-i", file_path, "-vf", vf, "-f", "null", "-"])

    with cd(folder):
        logger.debug(f"Extracting signature with {cmd}")
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


def extract_video_metadata(video):
    # type: (Union[str, BinaryIO]) -> dict
    """Extract basic metadata from video files."""
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

        lng = languages.pop() if len(languages) == 1 else list(languages)
        if lng:
            metadata["language"] = lng

        return dict(sorted(metadata.items()))


if __name__ == "__main__":
    import iscc_samples

    extract_video_preview(iscc_samples.videos()[0].as_posix())
