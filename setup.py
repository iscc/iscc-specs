#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The setup script."""
import re
from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


def version():
    version_file = 'src/iscc/__init__.py'
    with open(version_file) as f:
        version_data = f.read()
    m = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_data, re.M)
    if m:
        return m.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='iscc',
    version=version(),
    description="ISCC: Reference Implementation",
    long_description=readme(),
    author="Titusz Pan",
    author_email='tp@py7.de',
    url='https://github.com/iscc/iscc-specs',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=['xxhash==1.3.0', 'Pillow==5.4.1'],
    license='BSD 2-clause',
    zip_safe=False,
    keywords='iscc identifier media content hash blockchain similarity',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
