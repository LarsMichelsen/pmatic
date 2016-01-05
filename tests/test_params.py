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

from test_api_remote import TestRemoteAPI
from pmatic.entities import Channel, Device
from pmatic.params import Parameter
from pmatic import utils, PMException

class TestParameter(TestRemoteAPI):
    @pytest.fixture(scope="class")
    def p(self, API):
        channel = Channel(API, {
            'address': 'KEQ0970393:1',
        })
        return Parameter(channel, {
            'control': 'SWITCH.STATE',
            'operations': 7,
            'name': 'STATE',
            'min': '0',
            'default': '0',
            'max': '1',
            '_value': True,
            'tab_order': 0,
            'flags': 1,
            'unit': '',
            'type': 'BOOL',
            'id': 'STATE',
            'channel': channel,
        }, None)


    def test_attributes(self, p):
        assert p.control == "SWITCH.STATE"
        assert type(p.operations) == int
        assert p.operations == 7
        assert p.name == "STATE"
        assert p._value == "0"
        assert type(p.tab_order) == int
        assert type(p.flags) == int
        assert utils.is_text(p.unit)
        assert p.unit == ""
        assert p.type == "BOOL"
        assert p.id == "STATE"
        assert isinstance(p.channel, Channel)


    def test_from_api_value(self, p):
        p._from_api_value("X") == "X"


    def test_to_api_value(self, p):
        p._to_api_value("X") == "X"


    def test_validate(self, p):
        p._validate("X") == True


    def test_readable(self, p):
        assert p.readable == True

        p.operations = 4
        assert p.readable == False

        p.operations = 0
        assert p.readable == False

        p.operations = 3
        assert p.readable == True

        p.operations = 7


    def test_writable(self, p):
        assert p.writable == True

        p.operations = 4
        assert p.writable == False

        p.operations = 2
        assert p.writable == True

        p.operations = 7


    def test_title(self, p):
        assert p.title == "State"

        p.name = "X_XABC"
        assert p.title == "X Xabc"


    def test_value(self, p):
        assert p.value == p._value


    def test_value_setter(self, p):
        p.operations = 5
        with pytest.raises(PMException) as e:
            p.value = "XXX"
        assert 'can not be changed' in str(e.value)

        with pytest.raises(PMException) as e:
            assert p.set("YYY") == False
        assert 'can not be changed' in str(e.value)

        p.operations = 7
        p.datatype = "boolean" # fake for setting
        p.value = "false"

        p.set("false")


    def test_set_to_default(self, p):
        p.datatype = "boolean" # fake for setting
        p.value = "true"
        p.set_to_default()
        assert p.value == p.default


    def test_formated(self, p):
        assert p.formated() == "0"
        p.unit = "X"

        assert p.formated() == "0 X"

        p.unit = "%"
        assert p.formated() == "0%"

        p.unit = ""


    def test_magic_str_unicode_bytes(self, p):
        if utils.is_py3():
            assert utils.is_text(p.__str__())
            assert utils.is_byte_string(p.__bytes__())
        else:
            assert utils.is_byte_string(p.__str__())
            assert utils.is_text(p.__unicode__())

        assert str(p) == "0"
        assert bytes(p) == b"0"



class TestParameterFloat(TestRemoteAPI):
    @pytest.fixture(scope="class")
    def p(self, API):
        switch_state_channel = Device.get_devices(API, device_name="Büro-Lampe")[0].channels[0]
        return switch_state_channel.values["ON_TIME"]


    def test_attributes(self, p):
        assert p.type == "FLOAT"
        assert p.unit == "s"
        assert p.name == "ON_TIME"
        assert type(p.value) == float
        assert type(p.min) == float
        assert type(p.max) == float
        assert type(p.default) == float


    def test_from_api_value(self, p):
        assert p._from_api_value("0.00000000") == 0.0
        assert p._from_api_value("1.00000001") == 1.00000001
        assert p._from_api_value("1") == 1.0


    def test_to_api_value(self, p):
        assert p._to_api_value(1.0) == "1.00"
        assert p._to_api_value(1.001) == "1.00"
        assert p._to_api_value(999.124) == "999.12"


    def test_validate(self, p):
        assert p._validate(1.0) == True
        assert p._validate(1) == True
        with pytest.raises(PMException):
            p._validate(-1)
        with pytest.raises(PMException):
            p._validate(-1.0)
        with pytest.raises(PMException):
            p._validate(p.max+0.1)


    def test_formated(self, p):
        p._value = 1.0
        assert p.formated() == "1.00 s"
        p._value = 1.991
        assert p.formated() == "1.99 s"
        p._value = -1.991
        assert p.formated() == "-1.99 s"



class TestParameterBOOL(TestRemoteAPI):
    @pytest.fixture(scope="class")
    def p(self, API):
        switch_state_channel = Device.get_devices(API, device_name="Büro-Lampe")[0].channels[0]
        return switch_state_channel.values["STATE"]


    def test_attributes(self, p):
        assert p.type == "BOOL"
        assert p.unit == ""
        assert p.name == "STATE"
        assert type(p.value) == bool


    def test_from_api_value(self, p):
        assert p._from_api_value("0") == False
        assert p._from_api_value("1") == True


    def test_to_api_value(self, p):
        assert p._to_api_value(True) == "true"
        assert p._to_api_value(False) == "false"


    def test_validate(self, p):
        assert p._validate(True) == True
        assert p._validate(False) == True
        with pytest.raises(PMException):
            p._validate(None)

# FIXME: Create tests for specific parameter types
#class TestParameterINTEGER(Parameter):
#class TestParameterSTRING(Parameter):
#class TestParameterBOOL(Parameter):
#class TestParameterENUM(ParameterINTEGER):
#class TestParameterACTION(ParameterBOOL):
