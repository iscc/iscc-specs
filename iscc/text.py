# -*- coding: utf-8 -*-
from iscc.cdc import data_chunks


# Average number of characters per text chunk
AVG_SIZE_TEXT = 1024


def text_chunks(text: str, avg_size=AVG_SIZE_TEXT):
    """
    Generates variable sized text chunks (without leading BOM)
    """
    data = text.encode("utf-32-be")
    avg_size *= 4  # 4 bytes per character
    for chunk in data_chunks(data, avg_size=avg_size, utf32=True):
        yield chunk.decode("utf-32-be")
