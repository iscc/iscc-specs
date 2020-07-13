# -*- coding: utf-8 -*-
from collections import deque
from itertools import islice


def multi_slide(iterable, size=2, step=1, fillvalue=None):
    if size < 0 or step < 1:
        raise ValueError
    it = iter(iterable)
    q = deque(islice(it, size), maxlen=size)
    if not q:
        return
    q.extend(fillvalue for _ in range(size - len(q)))
    while True:
        yield iter(q)
        try:
            q.append(next(it))
        except StopIteration:
            return
        q.extend(next(it, fillvalue) for _ in range(step - 1))
