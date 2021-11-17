# -*- coding: utf-8 -*-
from iscc import utils


def test_sliding_window():
    assert list(utils.sliding_window("", width=4)) == [""]
    assert list(utils.sliding_window("A", width=4)) == ["A"]
    assert list(utils.sliding_window("Hello", width=4)) == ["Hell", "ello"]
    words = ("lorem", "ipsum", "dolor", "sit", "amet")
    slices = list(utils.sliding_window(words, 2))
    assert slices[0] == ("lorem", "ipsum")
    assert slices[1] == ("ipsum", "dolor")
    assert slices[-1] == ("sit", "amet")


def test_sliding_window_retains_sequence_type():
    tuple_sequence = ("lorem", "ipsum", "dolor", "sit", "amet")
    slices = list(utils.sliding_window(tuple_sequence, 2))
    assert isinstance(slices[0], tuple)

    list_sequence = list(tuple_sequence)
    slices = list(utils.sliding_window(list_sequence, 2))
    assert isinstance(slices[0], list)

    text_sequence = "lorem"
    slices = list(utils.sliding_window(text_sequence, 2))
    assert isinstance(slices[0], str)
    assert slices[0] == "lo"
    assert slices[1] == "or"
    assert slices[-1] == "em"


def test_sliding_window_bigger_than_sequence():
    words = ("lorem", "ipsum", "dolor", "sit", "amet")
    slices = list(utils.sliding_window(words, 6))
    assert slices[0] == words

    slices = list(utils.sliding_window("hello", 5))
    assert slices[0] == "hello"


def test_download_file(tmp_path):
    local_path = utils.download_file(
        "https://iscc.foundation/news/images/lib-arch-ottawa.jpg"
    )
    assert local_path.endswith("lib-arch-ottawa.jpg")


def test_download_file_domain_root(tmp_path):
    local_path = utils.download_file("https://iscc.foundation", folder=tmp_path)
    assert local_path.endswith("iscc.foundation")
