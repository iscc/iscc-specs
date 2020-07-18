# -*- coding: utf-8 -*-
from io import BytesIO


def static_bytes(n: int, block_size: int = 4) -> bytes:
    """Returns a deterministic inspectable bytesequence with counter bytes for testing.

    Source:
    https://github.com/oconnor663/bao/blob/master/tests/generate_input.py

    :param int n: Number of bytes to generate. (must be a multiple of block_sies)
    :param int block_size: Block size in bytes (blocks begin with a counter)
    :return bytes: deterministic bytestring
    """
    data = BytesIO()
    i = 1
    while n > 0:
        ibytes = i.to_bytes(block_size, "little")
        take = min(block_size, n)
        data.write(ibytes[:take])
        n -= take
        i += 1
    return data.getvalue()
