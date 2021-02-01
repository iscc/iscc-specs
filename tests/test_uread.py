# -*- coding: utf-8 -*-
from iscc import uread
from tests.test_readables import image_readables


def test_open_data():
    for readable in image_readables():
        f = uread.open_data(readable)
        assert f.read(10).hex() == "ffd8ffe116a445786966"
