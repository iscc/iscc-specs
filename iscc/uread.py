# -*- coding: utf-8 -*-
import io
from iscc.schema import Readable, Uri, File, Data
from iscc.utils import download_file
from tempfile import gettempdir


def open_data(data):
    # type: (Readable) -> Readable
    """Open filepath, uri, rawdata or file-like object."""
    if isinstance(data, Uri.__args__):
        if isinstance(data, str) and (
            data.startswith("http://") or data.startswith("https://")
        ):
            temp_folder = gettempdir()
            data = download_file(data, folder=temp_folder, sanitize=True)
        return open(str(data), "rb")
    elif isinstance(data, Data.__args__):
        return io.BytesIO(data)
    elif isinstance(data, File.__args__):
        data.seek(0)
        return data
    else:
        raise ValueError(f"unsupported data type {type(data)}")
