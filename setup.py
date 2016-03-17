#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - A simple API to to the Homematic CCU2
# Copyright (C) 2016 Lars Michelsen <lm@larsmichelsen.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='pmatic',
    version='0.1',
    description='A simple API to to the Homematic CCU2',
    maintainer='Lars Michelsen',
    maintainer_email='lm@larsmichelsen.com',
    url='https://larsmichelsen.github.io/pmatic/',
    download_url="https://pypi.python.org/pypi/pmatic",
    keywords="Homematic, Python, CCU, Automating, Scripting, Home Automation",
    long_description=read("README.rst"),
    platforms="Linux,CCU2",
    license='GPLv2',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=[
      'pmatic',
    ],
    data_files=[
        ('/usr/share/doc/pmatic', ['LICENSE', 'README.md']),
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-flakes', 'pytest-cache', 'beautifulsoup4'],
)
