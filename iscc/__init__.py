# -*- coding: utf-8 -*-
import os
import appdirs

__version__ = "1.0.5"
APP_NAME = "iscc"
APP_DIR = appdirs.user_data_dir(APP_NAME, roaming=False)
os.makedirs(APP_DIR, exist_ok=True)
os.environ["TIKA_PATH"] = APP_DIR
os.environ["TIKA_LOG_PATH"] = APP_DIR
os.environ["TIKA_STARTUP_MAX_RETRY"] = "8"
os.environ["LOGURU_AUTOINIT"] = "False"
from tika import tika

tika.log.disabled = True

from iscc.core import *
from iscc.params import *
from iscc.cdc import *
from iscc.minhash import *
from iscc.text import *
from iscc.metrics import distance
