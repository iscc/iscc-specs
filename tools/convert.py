# -*- coding: utf-8 -*-
"""Convert Specification to .docx.

Requires https://pandoc.org/ to be on path.
"""
import os
import subprocess

infiles = [
    "index.md",
    "features.md",
    "concept.md",
    "specification.md",
    "implementations.md",
    "license.md",
]


def main():
    os.chdir("../docs")
    cmd = ["pandoc", "-s", "-o", "../tools/iscc-specification.docx"] + infiles
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
