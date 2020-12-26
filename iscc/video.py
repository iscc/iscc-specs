# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from os.path import basename, dirname
import imageio_ffmpeg
from statistics import mode
from iscc.utils import cd


FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def compute_signature(file_path: str) -> bytes:
    """Computes MP7 Video Signature"""
    crop = detect_crop(file_path)
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


def detect_crop(file) -> str:
    """
    Detect crop value for video.
    Example result: crop=176:96:0:24
    """
    cmd = [FFMPEG, "-i", file, "-vf", "cropdetect", "-f", "null", "-"]
    res = subprocess.run(cmd, stderr=subprocess.PIPE)
    text = res.stderr.decode(encoding=sys.stdout.encoding)
    crops = [
        line.split()[-1]
        for line in text.splitlines()
        if line.startswith("[Parsed_cropdetect")
    ]
    return mode(crops)
