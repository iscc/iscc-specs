# -*- coding: utf-8 -*-
"""Configuration Prameters and Constants"""


# Component Headers
HEAD_MID = b"\x00"
HEAD_CID_T = b"\x10"
HEAD_CID_T_PCF = b"\x11"
HEAD_CID_I = b"\x12"
HEAD_CID_I_PCF = b"\x13"
HEAD_CID_A = b"\x14"
HEAD_CID_A_PCF = b"\x15"
HEAD_CID_V = b"\x16"
HEAD_CID_V_PCF = b"\x17"
HEAD_CID_M = b"\x18"
HEAD_CID_M_PCF = b"\x19"
HEAD_DID = b"\x20"
HEAD_IID = b"\x30"

# Algorithm Constants

# Instance-ID - Bytes to read per blake3 hash update.
IID_READ_SIZE = 524288


SYMBOLS = "C23456789rB1ZEFGTtYiAaVvMmHUPWXKDNbcdefghLjkSnopRqsJuQwxyz"
VALUES = "".join([chr(i) for i in range(58)])
C2VTABLE = str.maketrans(SYMBOLS, VALUES)
V2CTABLE = str.maketrans(VALUES, SYMBOLS)
# TRIM_TITLE = 128
# TRIM_EXTRA = 4096
WINDOW_SIZE_MID = 3
WINDOW_SIZE_CID_T = 13
