# -*- coding: utf-8 -*-
from iscc.text import text_chunks
from fauxfactory.factories.strings import gen_utf8


def test_text_chunks():
    txt = gen_utf8(1024 * 100)
    chunks = list(text_chunks(txt, avg_size=1024))
    assert "".join(chunks) == txt
