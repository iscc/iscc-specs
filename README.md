# ISCC Specification

The **International Standard Content Code** is an open standard for decentralized content identifiers. This repository contains the specification of the **ISCC Standard**. The latest published version can be found at [iscc.codes](http://iscc.codes)

## Install

The entire **ISCC Specification** is written in plain text [Markdown](https://en.wikipedia.org/wiki/Markdown). The markdown content is than built and published with the excellent [mkdoks](http://www.mkdocs.org/) documetation tool. If you have some basic command line skills you can build and run the specification site on your own computer. Make sure you have the [Git](https://git-scm.com/) and [Python](https://www.python.org/) installed on your system and follow these steps on the command line:

```shell
git clone https://github.com/coblo/iscc-specs.git
cd iscc-specs
pip install -r requirements.txt
mkdocs serve
```

## Usage

All specification documents can be found in the `./docs` subfolder or the repository. The recommended editor for the markdown files is [typora](https://typora.io/). If you have commit rights to the [main repository](https://github.com/coblo/iscc-specs) you can depoy the site with a simple `mkdocs gh-deploy`. 

## Contribute

Pull requests and other contributions are welcome. Use the [Github Issues](https://github.com/coblo/iscc-specs/issues) section of this project to ask questions or discuss ideas for the **ISCC Specification**.

## License

This repository is only for documents. All of these are licensed under the [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) license © 2017 Content Blockchain Project.
