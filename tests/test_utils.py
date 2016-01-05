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
from pmatic import utils


def test_is_string():
    assert utils.is_string("x")
    assert utils.is_string(1) == False
    assert utils.is_string(u"x")


def test_is_text():
    assert utils.is_text(str("x")) == False
    assert utils.is_text(1) == False
    assert utils.is_text(u"x") == True


def test_decamel():
    assert utils.decamel("thisIsACamelCase") == "this_is_a_camel_case"
    assert utils.decamel("thisIsACamelCase") == "this_is_a_camel_case"
    assert utils.decamel('CamelCamelCase') == "camel_camel_case"
    assert utils.decamel('Camel2Camel2Case') == 'camel2_camel2_case'
    assert utils.decamel('getHTTPResponseCode') == 'get_http_response_code'
    assert utils.decamel('get2HTTPResponseCode') == 'get2_http_response_code'
    assert utils.decamel('HTTPResponseCode') == 'http_response_code'
    assert utils.decamel('HTTPResponseCodeXYZ') == 'http_response_code_xyz'


def test_fmt_temperature():
    assert utils.fmt_temperature(0.0) == "0.00 °C"
    assert utils.fmt_temperature(1) == "1.00 °C"
    assert utils.fmt_temperature(9.1234) == "9.12 °C"

    with pytest.raises(Exception):
        assert utils.fmt_temperature(None)

    with pytest.raises(Exception):
        assert utils.fmt_temperature("1.2")


def test_fmt_humidity():
    assert utils.fmt_humidity(0) == "0%"
    assert utils.fmt_humidity(199) == "199%"
    assert utils.fmt_humidity(1.2) == "1%"
    assert utils.fmt_humidity(1.6) == "1%"

    with pytest.raises(Exception):
        assert utils.fmt_humidity(None)


def test_fmt_percentage_int():
    assert utils.fmt_percentage_int(0) == "0%"
    assert utils.fmt_percentage_int(199) == "199%"
    assert utils.fmt_percentage_int(1.2) == "1%"
    assert utils.fmt_percentage_int(1.6) == "1%"

    with pytest.raises(Exception):
        assert utils.fmt_percentage_int(None)
