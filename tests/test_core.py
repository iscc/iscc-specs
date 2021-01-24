# -*- coding: utf-8 -*-
import pytest
from iscc import core
from tests import HERE
from os.path import join


SAMPLE = join(HERE, "test.3gp")


def test_compute_raises():
    with pytest.raises(ValueError):
        core.compute(b"\xff" * 20)
