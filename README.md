# ISCC - Spec and Reference Code

[![Build](https://github.com/iscc/iscc-specs/actions/workflows/test.yml/badge.svg?branch=version-1.1)](https://github.com/iscc/iscc-specs/actions/workflows/test.yml)
[![License](https://img.shields.io/pypi/l/iscc.svg)](https://pypi.python.org/pypi/iscc/)
[![Downloads](https://pepy.tech/badge/iscc)](https://pepy.tech/project/iscc)
[![DOI](https://zenodo.org/badge/96668860.svg)](https://zenodo.org/badge/latestdoi/96668860)

The **International Standard Content Code** is a proposal for an [open standard](https://en.wikipedia.org/wiki/Open_standard) for decentralized content identification. This repository contains the specification of the proposed **ISCC Standard** and a reference implementation in Python3. The latest published version of the specification can be found at [iscc.codes](https://iscc.codes)

| NOTE: This is ISCC Version 1.1 work in progress!!! |
| --- |

## Installing the reference code

The reference code is published with the package name [iscc](https://pypi.python.org/pypi/iscc) on Python Package Index. Install it with:

``` bash
pip install iscc==1.1.0b12
```

If your system is setup to compile c-extensions install with:

``` bash
pip install iscc[turbo]==1.1.0b12
```

This will install cython and build binary extansions for faster ISCC processing.

To install the required binaries for content extraction do:

```python
from iscc.bin import install
install()
```

## Using the reference code

A short example on how to create an ISCC Code with the reference implementation.

``` python
>>> import iscc
>>> iscc.code_iscc("README.md", all_granular=True)
{'version': '0-0-0',
 'iscc': 'KADYHLZUJ43U3LX7G7PNLS54JHAET3ANW4EQ3YQIP3LDAZHEYIS5GWI',
 'title': '# ISCC Spec and Reference Code',
 'filename': 'README.md',
 'filesize': 3840,
 'mediatype': 'text/markdown',
 'tophash': '00194e2c4e5570e637bd18667740fdcf7f1683d6ccace7f5c0cc6531f6e982e5',
 'metahash': '828dd01bf76b78fc448f6d2ab25008835d2993c6acde205235dc942083c4677d',
 'datahash': 'd63064e4c225d3594bdf60c30bcb04554e53059d9077a6f330f8295b4420ded5',
 'gmt': <GMT.text: 'text'>,
 'characters': 3457,
 'language': 'en',
 'features': [{'kind': <FeatureType.data: 'data'>,
               'version': 0,
               'features': ['7A23CQ3iCH4'],
               'sizes': [3840]},
              {'kind': <FeatureType.text: 'text'>,
               'version': 0,
               'features': ['Nt6V67hJxmk',
                            '9HvPYqt1rQw',
                            'ld1FLbp7A50',
                            'M8aTn6atuB0'],
               'sizes': [2340, 309, 292, 516]}]}
```

## Working with the specification

| NOTE: This is ISCC Version 1.1 - The specs are not yet updated!!! |
| --- |

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
