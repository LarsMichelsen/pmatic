#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - A simple API to to the Homematic CCU2
# Copyright (C) 2015 Lars Michelsen <lm@larsmichelsen.com>
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


from setuptools import setup
import os

setup(name='pmatic',
    version='0.1',
    description='A simple API to to the Homematic CCU2',
    long_description='pmatic is a python library to provide access to the Homematic CCU2. You ' \
                     'can execute pmatic directly on the CCU2 or another system having Python ' \
                     'installed. With pmatic you can write your own Python scripts to communicate ' \
                     'with your CCU2 devices.',
    author='Lars Michelsen',
    author_email='lm@larsmichelsen.com',
    url='https://github.com/LaMi-/pmatic',
    license='GPLv2',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=[
      'pmatic',
      'pmatic.api',
    ],
    data_files=[
        ('/usr/share/doc/pmatic', ['LICENSE', 'README.md']),
    ],
    test_suite="tests",
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
