# -*- coding: utf-8 -*-
import os
from codetiming import Timer
from humanize import naturalsize
import iscc


GB1 = os.urandom(1048576 * 1000)


def benchmark(func, data):
    t = Timer(logger=None)
    num_bytes = len(data)
    t.start()
    result = list(func(data))
    t.stop()
    throughput = naturalsize(num_bytes / t.last)
    print("{}: {}/s".format(func.__name__, throughput))


benchmark(iscc.instance_id, GB1)
benchmark(iscc.data_chunks, GB1)
benchmark(iscc.data_id, GB1)
