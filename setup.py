#!/usr/bin/env python
from __future__ import with_statement

import sys
import subprocess

try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command
    from distutils.errors import CCompilerError, DistutilsExecError, \
        DistutilsPlatformError

VERSION = '1.0.4'
DESCRIPTION = "JSON decoder for Python that can extract data from the muck"

with open('README.rst', 'r') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name="dirtyjson",
    version=VERSION,
    packages=['dirtyjson', 'dirtyjson.tests'],
    author="Scott Maxwell",
    author_email="scott@codecobblers.com",
    url="https://github.com/codecobblers/dirtyjson",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    license="MIT License",
    classifiers=["Development Status :: 5 - Production/Stable",
                 "Intended Audience :: Developers",
                 "License :: OSI Approved :: MIT License",
                 "License :: OSI Approved :: Academic Free License (AFL)",
                 "Programming Language :: Python",
                 "Programming Language :: Python :: 2",
                 "Programming Language :: Python :: 2.5",
                 "Programming Language :: Python :: 2.6",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3.3",
                 "Programming Language :: Python :: 3.4",
                 "Programming Language :: Python :: Implementation :: CPython",
                 "Programming Language :: Python :: Implementation :: PyPy",
                 "Topic :: Software Development :: Libraries :: Python Modules"],
    platforms=['any'],
    test_suite="dirtyjson.tests",
    zip_safe=True)
