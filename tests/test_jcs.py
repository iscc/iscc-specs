# -*- coding: utf-8 -*-
import json
import iscc


def test_jcs_roundtrip():
    data = dict(
        text="  Iñtërnâtiôn\nàlizætiøn☃💩 –  is a tric\t ky \u00A0 thing!\r",
        number=361665416,
        fraction=65654.57354,
    )
    rt = iscc.roundtrip(data)
    assert list(rt.keys()) == ["fraction", "number", "text"]


def test_jsc_text_normalized():
    data = dict(
        text="Hello World!",
        number=361665416,
        fraction=65654.57354,
    )
    canonical = iscc.canonicalize(data)
    assert (
        canonical.decode("utf-8")
        == '{"fraction":65654.57354,"number":361665416,"text":"Hello World!"}'
    )

    assert (
        iscc.normalize_text(canonical)
        == '"fraction":65654.57354,"number":361665416,"text":"Hello World!"'
    )
