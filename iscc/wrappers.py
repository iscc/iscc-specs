# -*- coding: utf-8 -*-
"""Wrap iscc-core functions for more convenient inputs/outputs"""
from typing import Iterable, List
from iscc_core import codec


def decompose(iscc_code):
    # type: (codec.AnyISCC) -> List[codec.Code]
    """
    Wrap iscc_core.codec.decompose to handle more input types and return higher
    level Code object instead of plain ISCC strings.
    """
    if isinstance(iscc_code, str):
        iscc_code = codec.clean(iscc_code)
    code_obj = codec.Code(iscc_code)
    components = [codec.Code(c) for c in codec.decompose(code_obj.code)]
    return components
