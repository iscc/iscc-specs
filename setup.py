#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='iscc',
    version='0.9.9',
    description="ISCC: Reference Implementation",
    long_description=readme(),
    author="Titusz Pan",
    author_email='tp@py7.de',
    url='https://github.com/coblo/iscc-specs',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=['xxhash', 'Pillow'],
    license='BSD 2-clause',
    zip_safe=False,
    keywords='iscc identifier media content hash blockchain similarity',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
)
