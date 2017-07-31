#!/usr/bin/env python3

import re
from pathlib import Path

import os

from setuptools import setup, find_packages

ROOT_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(ROOT_DIR)

with (Path(__file__).parent / 'aiosparql' / '__init__.py').open() as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


with open('./test-requirements.txt') as test_reqs_txt:
    test_requirements = list(iter(test_reqs_txt))


long_description = open('README.rst').read()


setup(
    name="aiosparql",
    version=version,
    description="An asynchronous SPARQL library using aiohttp",
    long_description=long_description,
    url='https://github.com/aio-libs/aiosparql',
    packages=find_packages(exclude=["tests.*", "tests"]),
    install_requires=['aiohttp>=2.1.0'],
    tests_require=test_requirements,
    zip_safe=False,
    test_suite='tests',
    python_requires='>=3.5.0',
    license="Apache 2",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
    ],
    maintainer='Cecile Tonglet',
    maintainer_email='cecile.tonglet@gmail.com',
)
