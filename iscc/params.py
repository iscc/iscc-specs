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

# Unicode categories to remove during text normalization
UNICODE_FILTER = frozenset(
    {
        "Cc",
        "Cf",
        "Cn",
        "Co",
        "Cs",
        "Mc",
        "Me",
        "Mn",
        "Pc",
        "Pd",
        "Pe",
        "Pf",
        "Pi",
        "Po",
        "Ps",
    }
)

# Common Control Characters considered whitespace
CC_WHITESPACE = (
    "\u0009",  # Horizontal Tab (TAB)
    "\u000A",  # Linefeed (LF)
    "\u000D",  # Carriage Return (CR)
)

SYMBOLS = "C23456789rB1ZEFGTtYiAaVvMmHUPWXKDNbcdefghLjkSnopRqsJuQwxyz"
VALUES = "".join([chr(i) for i in range(58)])
C2VTABLE = str.maketrans(SYMBOLS, VALUES)
V2CTABLE = str.maketrans(VALUES, SYMBOLS)
INPUT_TRIM = 128
WINDOW_SIZE_MID = 4
WINDOW_SIZE_CID_T = 13
