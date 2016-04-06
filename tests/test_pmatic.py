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

import sys
import codecs
import pytest
import logging

import pmatic


def test_log_levels():
    assert pmatic.CRITICAL == logging.CRITICAL
    assert pmatic.ERROR == logging.ERROR
    assert pmatic.WARNING == logging.WARNING
    assert pmatic.INFO == logging.INFO
    assert pmatic.DEBUG == logging.DEBUG


def test_set_logging():
    pmatic.logging()
    l = logging.getLogger("pmatic")
    assert l.getEffectiveLevel() == pmatic.WARNING

    pmatic.logging(pmatic.CRITICAL)
    assert l.getEffectiveLevel() == pmatic.CRITICAL

    pmatic.logging()
    assert l.getEffectiveLevel() == pmatic.WARNING


def test_log(capfd):
    pmatic.logging()

    l = logging.getLogger("pmatic")
    l.log(pmatic.CRITICAL, "Dingelingpiffpaff")

    out, err = capfd.readouterr()
    assert "[CRITICAL] Dingelingpiffpaff" in err
    assert out == ""


def test_unlogged_log(capfd):
    pmatic.logging()

    l = logging.getLogger("pmatic")
    l.log(pmatic.DEBUG, "Dingelingpiffpaff hoho")
    out, err = capfd.readouterr()
    assert "Dingelingpiffpaff" not in err
    assert out == ""

    l.log(pmatic.INFO, "Dingelingpiffpaff hoho")
    out, err = capfd.readouterr()
    assert "Dingelingpiffpaff" not in err
    assert out == ""


@pytest.mark.skipif(sys.version_info >= (3,0),
                    reason="requires python2.7")
def test_fix_python2_pipe_encoding(monkeypatch):
    null = codecs.open("/dev/null", "w", encoding=None)
    monkeypatch.setattr(sys, "stdout", null)
    monkeypatch.setattr(sys, "stderr", null)
    assert sys.stdout == null
    assert sys.stderr == null

    pmatic.fix_python2_pipe_encoding()

    assert "utf_8.StreamWriter" in repr(sys.stdout.__class__)
    assert "utf_8.StreamWriter" in repr(sys.stderr.__class__)
