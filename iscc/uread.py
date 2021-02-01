# -*- coding: utf-8 -*-
import io
from typing import Union
from iscc.schema import Readable, Uri, File, Data
from typing import BinaryIO


def open_data(data):
    # type: (Readable) -> Union[BinaryIO]
    """Open filepath, rawdata or file-like object."""
    if isinstance(data, Uri.__args__):
        return open(str(data), "rb")
    elif isinstance(data, Data.__args__):
        return io.BytesIO(data)
    elif isinstance(data, File.__args__):
        data.seek(0)
        return data
    else:
        raise ValueError(f"Unupported data type {type(data)}")
