# -*- coding: utf-8 -*-
__version__ = "1.1.0b12"
import os
from pathlib import Path
import click


HERE = Path(__file__).parent
APP_NAME = "iscc"
APP_DIR = click.get_app_dir(APP_NAME, roaming=False)
os.makedirs(APP_DIR, exist_ok=True)
os.environ["TIKA_STARTUP_MAX_RETRY"] = "20"
os.environ["LOGURU_AUTOINIT"] = "False"

from tika import tika

tika.log.disabled = True

from iscc.api import (
    code_iscc,
    code_meta,
    code_content,
    code_text,
    code_image,
    code_audio,
    code_video,
    code_data,
    code_instance,
    code_iscc_id,
)

from iscc import (
    text,
    image,
    audio,
    video,
    match,
    metrics,
    mediatype,
    utils,
    bin,
    data,
    index,
    jcs,
    uread,
    utils,
)
