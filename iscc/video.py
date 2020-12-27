# -*- coding: utf-8 -*-
import subprocess
from loguru import logger as log
import os
import sys
from subprocess import Popen, PIPE, DEVNULL
from os.path import basename, dirname
from secrets import token_hex
from typing import Generator
import imageio_ffmpeg
from statistics import mode
from iscc.utils import cd


FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def compute_signature(file_path: str, crop=None) -> bytes:
    """Computes MP7 Video Signature"""
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


def signature_generator() -> Generator:
    """Streaming signature generator (use gen.send(chunk)."""

    def raw_generator():
        sigfile = token_hex(16) + ".bin"
        log.info(sigfile)
        vf = "signature=format=binary:filename={}".format(sigfile)
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

    initialized_generator = raw_generator()
    next(initialized_generator)
    return initialized_generator


def detect_crop(file_path: str) -> str:
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
