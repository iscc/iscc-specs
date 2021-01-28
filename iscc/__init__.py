# -*- coding: utf-8 -*-
import os
from pathlib import Path

HERE = Path(__file__).parent
TIKA_BIN = HERE / "tika-server-1.25.jar"
__version__ = "1.0.5"

os.environ["TIKA_SERVER_JAR"] = TIKA_BIN.as_uri()
os.environ["TIKA_STARTUP_MAX_RETRY"] = "12"
os.environ["LOGURU_AUTOINIT"] = "False"
from tika import tika

tika.log.disabled = True

from iscc.core import *
from iscc.params import *
from iscc.cdc import *
from iscc.minhash import *
from iscc.text import *
from iscc.metrics import distance
