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

IS_PYPY = hasattr(sys, 'pypy_translation_info')
VERSION = '1.0.0'
DESCRIPTION = "JSON decoder for Python that can extract data from the muck"

with open('README.rst', 'r') as f:
    LONG_DESCRIPTION = f.read()

CLASSIFIERS = filter(None, map(str.strip,
                               """
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
License :: OSI Approved :: MIT License
License :: OSI Approved :: Academic Free License (AFL)
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.5
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: PyPy
Topic :: Software Development :: Libraries :: Python Modules
""".splitlines()))


class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        raise SystemExit(
            subprocess.call([sys.executable,
                             # Turn on deprecation warnings
                             '-Wd',
                             'dirtyjson/tests/__init__.py']))


setup(
    name="dirtyjson",
    version=VERSION,
    cmdclass=dict(test=TestCommand),
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    author="Scott Maxwell",
    author_email="scott@codecobblers.com",
    url="http://github.com/codecobblers/dirtyjson",
    license="MIT License",
    packages=['dirtyjson', 'dirtyjson.tests'],
    platforms=['any'])
