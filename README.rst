==================
ISCC Specification
==================

|status| |license|

.. |status| image:: https://img.shields.io/pypi/v/iscc.svg
   :target: https://pypi.python.org/pypi/iscc/
   :alt: PyPI Status
.. |license| image:: https://img.shields.io/pypi/l/iscc.svg
   :target: https://pypi.python.org/pypi/iscc/
   :alt: PyPI License

The **International Standard Content Code** is an [open standard](https://en.wikipedia.org/wiki/Open_standard) for decentralized content identifiers. This repository contains the specification of the **ISCC Standard** and a minima reference implementation in Python3. The latest published version of the specification can be found at [iscc.codes](http://iscc.codes)

Install
=======

The entire **ISCC Specification** is written in plain text [Markdown](https://en.wikipedia.org/wiki/Markdown). The markdown content is than built and published with the excellent [mkdocs](http://www.mkdocs.org/) documetation tool. If you have some basic command line skills you can build and run the specification site on your own computer. Make sure you have the [Git](https://git-scm.com/) and [Python](https://www.python.org/) installed on your system and follow these steps on the command line:

.. code-block:: bash

    git clone https://github.com/coblo/iscc-specs.git
    cd iscc-specs
    pip install -r requirements.txt
    mkdocs serve


Usage
=====

All specification documents can be found in the `./docs` subfolder or the repository. The recommended editor for the markdown files is [typora](https://typora.io/). If you have commit rights to the [main repository](https://github.com/coblo/iscc-specs) you can deploy the site with a simple `mkdocs gh-deploy`.

Contribute
==========

Pull requests and other contributions are welcome. Use the [Github Issues](https://github.com/coblo/iscc-specs/issues) section of this project to ask questions or discuss ideas for the **ISCC Specification**.

License
=======

All of documentation is licensed under the [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) license © 2017 Content Blockchain Project.
Reference code is licensed under BSD-2-Clause.
