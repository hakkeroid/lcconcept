#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from setuptools import setup, find_packages

REQUIREMENTS = [
    'six',
]


setup(
    name='lcconcept',
    version='0.0.0',
    description='Manages configuration coming from config files, environment variables, command line arguments, code defaults or other sources',
    author='Philipp Busch',
    author_email='hakkeroid@philippbusch.de',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    license="BSD",
    zip_safe=False,
    keywords='configuration',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
    ],

    install_requires=REQUIREMENTS,
)
