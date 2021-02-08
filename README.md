# ISCC - Spec and Reference Code

[![Build](https://travis-ci.org/iscc/iscc-specs.svg?branch=master)](https://travis-ci.org/iscc/iscc-specs)
[![Version](https://img.shields.io/pypi/v/iscc.svg)](https://pypi.python.org/pypi/iscc/)
[![License](https://img.shields.io/pypi/l/iscc.svg)](https://pypi.python.org/pypi/iscc/)
[![Downloads](https://pepy.tech/badge/iscc)](https://pepy.tech/project/iscc)
[![DOI](https://zenodo.org/badge/96668860.svg)](https://zenodo.org/badge/latestdoi/96668860)

The **International Standard Content Code** is a proposal for an [open standard](https://en.wikipedia.org/wiki/Open_standard) for decentralized content identification. This repository contains the specification of the proposed **ISCC Standard** and a reference implementation in Python3. The latest published version of the specification can be found at [iscc.codes](https://iscc.codes)

| NOTE: This is ISCC Version 1.1 work in progress!!! |
| --- |

## Installing the reference code

The reference code is published with the package name [iscc](https://pypi.python.org/pypi/iscc) on Python Package Index. Install it with:

``` bash
pip install iscc
```

## Using the reference code

A short example on how to create an ISCC Code with the reference implementation.

``` python
>>> import iscc
>>> iscc.code_iscc("README.md")
{
    'characters': 2918,
    'datahash': 'd30edda59fd4803ad0d2754fcbda1ec4097d12bd790b10cd610a24764cfcef16',
    'filename': 'README.md',
    'filesize': 3075,
    'gmt': 'text',
    'iscc': 'KADYHLZUJ43U3LX7C6P5LSJ7JHAETKCYHYCQ5YX4C3JQ5XNFT7KIAOQ',
    'language': 'en',
    'mediatype': 'text/markdown',
    'metahash': '828dd01bf76b78fc448f6d2ab25008835d2993c6acde205235dc942083c4677d',
    'title': '# ISCC Spec and Reference Code'
 }
```

## Working with the specification

The entire **ISCC Specification** is written in plain text [Markdown](https://en.wikipedia.org/wiki/Markdown). The markdown content is than built and published with the excellent [mkdocs](http://www.mkdocs.org/) documetation tool. If you have some basic command line skills you can build and run the specification site on your own computer. Make sure you have the [git](https://git-scm.com/) and [Python](https://www.python.org/) and [Poetry](https://pypi.org/project/poetry/) installed on your system and follow these steps on the command line:

``` bash
git clone https://github.com/iscc/iscc-specs.git
cd iscc-specs
poetry install
mkdocs serve
```

All specification documents can be found in the `./docs` subfolder or the repository. The recommended editor for the markdown files is [Typora](https://typora.io/). If you have commit rights to the [main repository](https://github.com/iscc/iscc-specs) you can deploy the site with a simple `mkdocs gh-deploy`.

## Contribute

Pull requests and other contributions are welcome. Use the [Github Issues](https://github.com/iscc/iscc-specs/issues) section of this project to discuss ideas for the **ISCC Specification**. You may also want  join our developer chat on Telegram at <https://t.me/iscc_dev>.

## License

All of documentation is licensed under the [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Reference code is licensed under BSD-2-Clause.
