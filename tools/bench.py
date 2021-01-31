# -*- coding: utf-8 -*-
import os
from codetiming import Timer
from humanize import naturalsize
import iscc
from fauxfactory.factories.strings import gen_utf8


GB1 = os.urandom(1048576 * 1000)
TXT = gen_utf8(500_000)


def benchmark(func, data):
    t = Timer(logger=None)
    num_bytes = len(data)
    t.start()
    _ = list(func(data))
    t.stop()
    throughput = naturalsize(num_bytes / t.last)
    print(
        "{:<18} {:>8}/s ({} for {})".format(
            func.__name__ + ":",
            throughput,
            t.text.format(t.last),
            naturalsize(num_bytes),
        )
    )


benchmark(iscc.code_instance, GB1)
benchmark(iscc.data_chunks, GB1)
benchmark(iscc.code_data, GB1)
benchmark(iscc.code_text, TXT)
benchmark(iscc.text_normalize, TXT)
