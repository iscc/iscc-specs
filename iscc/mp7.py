# -*- coding: utf-8 -*-
"""
  ffmpeg signature parsing based on binary_export function from:
     https://www.ffmpeg.org/doxygen/3.4/vf__signature_8c_source.html

"""
import datetime
from dataclasses import dataclass
from fractions import Fraction
from typing import Tuple, List
import numpy as np
from loguru import logger

# try loading optional jit compiler for speedup
try:
    from numba import jit, njit

    if __name__ == "__main__":
        logger.debug("using numba engine for jit compiling")
except ImportError:

    def jit(func):
        def do_nothing(*args, **kwargs):
            return func(*args, **kwargs)

        return do_nothing

    if __name__ == "__main__":
        logger.debug("can not load numba lib")


@dataclass
class FFMpegFrameSignature:
    """datatype to return by read_ffmpeg_signature"""

    vectors: np.ndarray  # 380 vectors, range: 0..2
    elapsed: Fraction  # time elapsed since start of video
    confidence: int  # signature confidence, range: 0..255


@jit
def to_binary(byte_data: bytes) -> np.ndarray:
    """convert each byte into a 8 bytes containing 1/0 value"""
    np_byte_data = np.frombuffer(byte_data, dtype=np.uint8)
    binary_data = np.zeros((len(byte_data) * 8,), dtype=np.uint8)
    p = 0
    for i, b in enumerate(np_byte_data):
        for ii in range(7, -1, -1):
            binary_data[p + ii] = b & 1
            b >>= 1
        p += 8
    return binary_data


@jit
def pop_bits(data_bits: np.ndarray, pos: int, bits: int = 32) -> Tuple[int, int]:
    """take out 0/1 values and pack them again to an unsigned integer
    :param data_bits: 0/1 data
    :param pos: position in 0/1 data
    :param bits: number of bits
    :return: value, new position
    """
    value = 0
    for i in range(bits):
        value = value + value + data_bits[pos + i]
    pos += bits
    return value, pos


@jit
def pop_bit(data_bits: np.ndarray, pos: int) -> Tuple[int, int]:
    """take out 1 bit of 0/1 values
    :param data_bits: 0/1 data
    :param pos: position in 0/1 data
    :return: take out just one bit
    """
    value = data_bits[pos]
    pos += 1
    return value, pos


@jit
def calc_byte_to_bit3() -> np.ndarray:
    """lookup table
    :return: table to convert a 8bit value into five three-bit-values
    """
    table_3_bit = np.zeros((256, 5), dtype=np.uint8)
    for i in range(256):
        div3 = 3 * 3 * 3 * 3
        for iii in range(0, 5):
            table_3_bit[i, iii] = (i // div3) % 3
            div3 //= 3
    return table_3_bit


SIGELEM_SIZE = 380


@jit
def nada(_):
    pass


@jit
def _read_ffmpeg_signature(
    byte_data: bytes, test_mode: bool, debug=nada
) -> Tuple[List[np.ndarray], List[int], List[int], List[int]]:
    """read data from the binary FFMpeg signature
        return lists of: vectors, elapsed time, confidence
        there is one entry for each frame.
    :param byte_data: actual ffmpeg signature data
    :param test_mode: basic data assert verification, print out details
    :return: [vectors],[elapsed time],[confidence]
    """

    table_3_bit = calc_byte_to_bit3()
    data_bits = to_binary(byte_data)
    pos = 0

    if test_mode:
        # put_bits32(&buf, 1); /* NumOfSpatial Regions, only 1 supported */
        _, pos = pop_bits(data_bits, pos)
        assert _ == 1
        # put_bits(&buf, 1, 1); /* SpatialLocationFlag, always the whole image */
        debug("expect 1 " + str(pop_bits(data_bits, pos, 1)[0]))
        pos += 1
        # put_bits32(&buf, 0); /* PixelX,1 PixelY,1, 0,0 */
        debug("expect 0 " + str(pop_bits(data_bits, pos)[0]))
        pos += 32
        # put_bits(&buf, 16, sc->w-1 & 0xFFFF); /* PixelX,2 */
        debug("expect X " + str(pop_bits(data_bits, pos, 16)[0]))
        pos += 16
        # put_bits(&buf, 16, sc->h-1 & 0xFFFF); /* PixelY,2 */
        debug("expect Y " + str(pop_bits(data_bits, pos, 16)[0]))
        pos += 16
        # put_bits32(&buf, 0); /* StartFrameOfSpatialRegion */
        debug("expect StartFrameOfSpatialRegion " + str(pop_bits(data_bits, pos)[0]))
        pos += 32
        # put_bits32(&buf, sc->lastindex); /* NumOfFrames */
    else:
        pos += 129

    num_of_frames, pos = pop_bits(data_bits, pos)
    media_time_unit, pos = pop_bits(data_bits, pos, 16)
    if test_mode:
        debug("expect MediaTimeUnit on second takes x units: " + str(media_time_unit))
        debug("expect num_of_frames " + str(num_of_frames))
        # /* hoping num is 1, other values are vague */
        # /* den/num might be greater than 16 bit, so cutting it */
        # put_bits(&buf, 16, 0xFFFF & (sc->time_base.den / sc->time_base.num)); /* MediaTimeUnit */
    if test_mode:
        # put_bits(&buf, 1, 1); /* MediaTimeFlagOfSpatialRegion */
        debug(
            "expect MediaTimeFlagOfSpatialRegion " + str(pop_bits(data_bits, pos, 1)[0])
        )
        pos += 1
        # put_bits32(&buf, 0); /* StartMediaTimeOfSpatialRegion */
        _, pos = pop_bits(data_bits, pos)
        assert _ == 0
        # put_bits32(&buf, 0xFFFFFFFF & sc->coarseend->last->pts); /* EndMediaTimeOfSpatialRegion */
        debug("expect  " + str(pop_bits(data_bits, pos)[0]))
        pos += 32
        # put_bits32(&buf, numofsegments); /* NumOfSegments */
    else:
        pos += 1 + 32 + 32

    num_of_segments, pos = pop_bits(data_bits, pos)
    if test_mode:
        debug("expect num_of_segments " + str(num_of_segments))
    pos += num_of_segments * (4 * 32 + 1 + 5 * 243)

    if test_mode:
        # /* fine signatures */
        # put_bits(&buf, 1, 0); /* CompressionFlag, only 0 supported */
        debug("expect compression " + str(pop_bits(data_bits, pos, 1)[0]))
        pos += 1
    else:
        pos += 1

    frame_sigs_v = []
    frame_sigs_c = []
    frame_sigs_e = []
    frame_sigs_tu = []
    # for (fs = sc->finesiglist; fs; fs = fs->next) {
    for i in range(num_of_frames):
        if test_mode:
            # put_bits(&buf, 1, 1); /* MediaTimeFlagOfFrame */
            _, pos = pop_bits(data_bits, pos, 1)
            assert _ == 1
            # put_bits32(&buf, 0xFFFFFFFF & fs->pts); /* MediaTimeOfFrame */
            raw_media_time, pos = pop_bits(data_bits, pos)

            debug("MediaTimeOfFrame  " + str(raw_media_time // media_time_unit))
            # put_bits(&buf, 8, fs->confidence); /* FrameConfidence */
            frame_confidence, pos = pop_bits(data_bits, pos, 8)
            debug("FrameConfidence " + str(frame_confidence))
        else:
            pos += 1
            raw_media_time, pos = pop_bits(data_bits, pos)
            frame_confidence, pos = pop_bits(data_bits, pos, 8)

        if test_mode:
            s = ""
            # for (i = 0; i < 5; i++)
            for ii in range(5):
                # put_bits(&buf, 8, fs->words[i]); /* Words */
                s += str(pop_bits(data_bits, pos, 8)[0]) + " "
                pos += 8
            debug(s)
        else:
            pos += 5 * 8

        vec = np.zeros((SIGELEM_SIZE,), dtype=np.uint8)
        p = 0
        for ii in range(SIGELEM_SIZE // 5):
            dat, pos = pop_bits(data_bits, pos, 8)
            vec[p : p + 5] = table_3_bit[dat]
            p += 5
        frame_sigs_v.append(vec)
        frame_sigs_e.append(raw_media_time)
        frame_sigs_c.append(frame_confidence)
        frame_sigs_tu.append(media_time_unit)
        if test_mode:
            debug(vec)
            # /* frame signature */
            # for (i = 0; i < SIGELEM_SIZE/5; i++) {
            #     put_bits(&buf, 8, fs->framesig[i]);

    return frame_sigs_v, frame_sigs_e, frame_sigs_c, frame_sigs_tu


def read_ffmpeg_signature(
    byte_data: bytes, test_mode=False
) -> List[FFMpegFrameSignature]:
    """wrapper for _read_ffmpeg_signature as numba code can not return a dataclass

    :param byte_data: actual ffmpeg signature data
    :param test_mode: basic data assert verification, print out details
    :return: [FFMpegFrameSignature()]
    """
    if test_mode:
        l = _read_ffmpeg_signature(byte_data, test_mode, debug=logger.debug)
    else:
        l = _read_ffmpeg_signature(byte_data, test_mode)
    frame_signatures = []
    for v, e, c, tu in zip(*l):
        frame_signatures.append(
            FFMpegFrameSignature(vectors=v, elapsed=Fraction(e, tu), confidence=c)
        )
    return frame_signatures


if __name__ == "__main__":
    signature_byte_data = open("../tests/ffmpeg_signature.bin", "rb").read()

    logger.debug("run speed test")
    import time

    # without the jit compiling..
    _ = read_ffmpeg_signature(byte_data=signature_byte_data)

    start = time.time()
    frame_signature = read_ffmpeg_signature(byte_data=signature_byte_data)
    duration = time.time() - start
    logger.debug(
        f"extracted signatures from {len(frame_signature)} frames in {duration:.3f} seconds."
    )
    logger.debug(f"{1e9 * duration / len(frame_signature):.0f} nano seconds/frame.")
