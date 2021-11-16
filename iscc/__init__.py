# -*- coding: utf-8 -*-
import os
from pathlib import Path
import click

__version__ = "1.1.0b8"

HERE = Path(__file__).parent
APP_NAME = "iscc"
APP_DIR = click.get_app_dir(APP_NAME, roaming=False)
os.makedirs(APP_DIR, exist_ok=True)
os.environ["TIKA_STARTUP_MAX_RETRY"] = "20"
os.environ["LOGURU_AUTOINIT"] = "False"

from tika import tika

tika.log.disabled = True

from iscc.core import *
from iscc.metrics import *
from iscc.image import *
from iscc.minhash import minhash
from iscc.text import *
from iscc.wtahash import *
from iscc.data import *
from iscc.codec import *
from iscc.video import *
from iscc.jcs import *
from iscc.match import *
from iscc.mediatype import *
from iscc.index import *
