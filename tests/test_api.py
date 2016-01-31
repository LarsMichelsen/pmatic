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

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytest

from pmatic import PMException
import pmatic.api
import os

def test_implicit_remote_init_missing_args():
    with pytest.raises(PMException):
        pmatic.api.init()


def test_explicit_remote_init_missing_args():
    with pytest.raises(PMException):
        pmatic.api.init("remote")


def test_explicit_local_init_but_remote():
    with pytest.raises(PMException):
        pmatic.api.init("local")


def test_explicit_local_enforce():
    orig_is_ccu = pmatic.api.is_ccu
    pmatic.api.is_ccu = lambda: True

    with pytest.raises(PMException):
        pmatic.api.init("local")

    pmatic.api.is_ccu = orig_is_ccu


def test_explicit_wrong_init():
    with pytest.raises(PMException):
        pmatic.api.init("WTF?!")


def test_local_remote_detection():
    orig_uname = os.uname

    os.uname = lambda: ('Linux', 'dev', '3.16.0-4-amd64',
                        '#1 SMP Debian 3.16.7-ckt9-3~deb8u1 (2015-04-24)', 'x86_64')
    assert not pmatic.api.is_ccu()

    os.uname = lambda: ('Linux', 'ccu', '3.4.11.ccu2',
                        '#1 PREEMPT Fri Oct 16 10:43:35 CEST 2015', 'armv5tejl')
    assert pmatic.api.is_ccu()

    os.uname = orig_uname
