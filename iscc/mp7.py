# -*- coding: utf-8 -*-
from dataclasses import dataclass
from fractions import Fraction
from typing import Tuple
from bitarray import bitarray
import bitarray
from bitarray.util import ba2int
import numpy as np


SIGELEM_SIZE = 380


@dataclass
class Frame:
    """datatype to return by read_ffmpeg_signature"""

    vector: np.ndarray  # 380 dimensional vector, range: 0..2
    elapsed: Fraction  # time elapsed since start of video
    confidence: int  # signature confidence, range: 0..255


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


def pop_bits(data_bits: bitarray, pos: int, bits: int = 32) -> Tuple[int, int]:
    """take out 0/1 values and pack them again to an unsigned integer
    :param data_bits: 0/1 data
    :param pos: position in 0/1 data
    :param bits: number of bits
    :return: value, new position
    """
    chunk = data_bits[pos : pos + bits]
    value = ba2int(chunk, signed=False)
    pos += bits
    return value, pos


def read_ffmpeg_signature(byte_data: bytes):
    table_3_bit = calc_byte_to_bit3()
    data_bits = bitarray.bitarray()
    data_bits.frombytes(byte_data)
    pos = 0
    pos += 129
    num_of_frames, pos = pop_bits(data_bits, pos)
    media_time_unit, pos = pop_bits(data_bits, pos, 16)
    pos += 1 + 32 + 32
    num_of_segments, pos = pop_bits(data_bits, pos)
    pos += num_of_segments * (4 * 32 + 1 + 5 * 243)
    pos += 1
    frame_sigs_v = []
    frame_sigs_c = []
    frame_sigs_e = []
    frame_sigs_tu = []
    for i in range(num_of_frames):
        pos += 1
        raw_media_time, pos = pop_bits(data_bits, pos)
        frame_confidence, pos = pop_bits(data_bits, pos, 8)
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

    fsigs = []
    r = (frame_sigs_v, frame_sigs_e, frame_sigs_c, frame_sigs_tu)
    for v, e, c, tu in zip(*r):
        fsigs.append(Frame(vector=v, elapsed=Fraction(e, tu), confidence=c))
    return fsigs


if __name__ == "__main__":
    from loguru import logger

    signature_byte_data = open("../tests/ffmpeg_signature.bin", "rb").read()
    logger.debug("run speed test")
    import time

    start = time.time()
    frame_signature = read_ffmpeg_signature(byte_data=signature_byte_data)
    duration = time.time() - start
    logger.debug(
        f"extracted signatures from {len(frame_signature)} frames in {duration:.3f} seconds."
    )
    logger.debug(f"{1e9 * duration / len(frame_signature):.0f} nano seconds/frame.")
