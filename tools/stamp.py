# -*- coding: utf-8 -*-
"""Generate an ISCC-Text for this specification"""
from os import walk, chdir
from os.path import dirname, join
import iscc
from subprocess import call


PROJECT_DIR = dirname(dirname(__file__))


def get_content(mode="text"):

    chdir(PROJECT_DIR)
    call(["mkdocs", "build"])

    content = "" if mode == "text" else b""
    if mode == "text":
        for root, dirs, files in walk(join(PROJECT_DIR, "docs")):
            for f in files:
                if f.endswith(".md"):
                    path = join(root, f)
                    with open(path, "r", encoding="utf-8") as textfile:
                        content += textfile.read()
    if mode == "data":
        for root, dirs, files in walk(join(PROJECT_DIR, "site")):
            for f in files:
                path = join(root, f)
                with open(path, "rb") as datafile:
                    content += datafile.read()

    return content


def spec_iscc():
    title = "ISCC - Specification"
    text = open(join(PROJECT_DIR, "docs/specification.md"), encoding="utf-8").read()
    data = open(join(PROJECT_DIR, "docs/specification.md"), "rb").read()
    mid, title, extra = iscc.meta_id(title)
    cidt = iscc.content_id_text(text)
    did = iscc.data_id(data)
    iid, hash_ = iscc.instance_id(data)
    code = "-".join((mid, cidt, did, iid))
    print("SPEC:")
    print("TITLE:", title, extra)
    print("ISCC:", code)
    print("IIDF:", hash_)


def site_iscc():
    title = "ISCC - Content Identifiers"
    text = get_content("text")
    data = get_content("data")
    mid, title, extra = iscc.meta_id(title)
    cidt = iscc.content_id_text(text)
    did = iscc.data_id(data)
    iid, hash_ = iscc.instance_id(data)
    code = "-".join((mid, cidt, did, iid))
    print("SITE:")
    print("TITLE:", title, extra)
    print("ISCC:", code)
    print("IIDF:", hash_)


if __name__ == "__main__":
    spec_iscc()
    site_iscc()
