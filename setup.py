#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

# Load the package's __version__.py module as a dictionary.
pkg = {}
with open(os.path.join(here, 'bison', '__version__.py')) as f:
    exec(f.read(), pkg)

# Load the README
with open('README.md', 'r') as f:
    readme = f.read()


setup(
    name=pkg['__title__'],
    version=pkg['__version__'],
    description=pkg['__description__'],
    long_description=readme,
    author=pkg['__author__'],
    author_email=pkg['__author_email__'],
    url=pkg['__url__'],
    license=pkg['__license__'],
    packages=find_packages(),
    package_data={'': ['LICENSE']},
    package_dir={'bison': 'bison'},
    include_package_data=True,
    python_requires=">=3.4",
    install_requires=[
        'pyyaml'
    ],
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    tests_require=[
        'pytest>=2.8.0',
        'pytest-cov'
    ]
)
