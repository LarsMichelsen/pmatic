#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - Python API for Homematic. Easy to use.
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

import time
import pytest

from pmatic.entities import Channel, Device, ChannelKey
from pmatic.params import Parameter, ParameterINTEGER, ParameterFLOAT, \
                          ParameterBOOL, ParameterACTION, ParameterSTRING, \
                          ParameterENUM
from pmatic import utils, PMException, PMActionFailed
import lib

class TestParameter(lib.TestCCUClassWide):
    @pytest.fixture(scope="function")
    def p(self, ccu):
        device = Device(ccu, {
            'address': 'KEQ0970393',
            #'children': ['KEQ0970393:0',
            #             'KEQ0970393:1',
            #             'KEQ0970393:2',
            #             'KEQ0970393:3',
            #             'KEQ0970393:4',
            #             'KEQ0970393:5',
            #             'KEQ0970393:6',
            'firmware': '1.4',
            'flags': 1,
            'interface': 'KEQ0714972',
            #'paramsets': ['MASTER'],
            'roaming': False,
            'type': 'HM-ES-PMSw1-Pl',
            'updatable': '1',
            'version': 1,
            'channels': [],
        })

        channel = Channel(device, {
            'address': 'KEQ0970393:1',
            'direction': 1,
            'flags': 1,
            'index': 1,
            'link_source_roles': [
                'KEYMATIC',
                'SWITCH',
                'WINDOW_SWITCH_RECEIVER',
                'WINMATIC'
            ],
            'link_target_roles': [],
            'paramsets': ['LINK', 'MASTER', 'VALUES'],
            'type': 'SHUTTER_CONTACT',
            'version': 15,
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
        })


    def test_attributes(self, p):
        assert p.control == "SWITCH.STATE"
        assert isinstance(p.operations, int)
        assert p.operations == 7
        assert p.internal_name == "STATE"
        assert p.name == "State"
        assert p._value == "0"
        assert isinstance(p.tab_order, int)
        assert isinstance(p.flags, int)
        assert utils.is_text(p.unit)
        assert p.unit == ""
        assert p.type == "BOOL"
        assert p.id == "STATE"
        assert isinstance(p.channel, Channel)


    def test_from_api_value(self, p):
        assert p._from_api_value("X") == "X"


    def test_to_api_value(self, p):
        assert p._to_api_value("X") == "X"


    def test_validate(self, p):
        assert p._validate("X") == True


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


    def test_supports_events(self, p):
        assert p.supports_events == True

        p.operations = 4
        assert p.supports_events == True

        p.operations = 2
        assert p.supports_events == False

        p.operations = 7


    def test_name(self, p):
        assert p.name == "State"

        p.internal_name = "X_XABC"
        assert p.internal_name == "X_XABC"
        assert p.name == "X Xabc"


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


    def test_value_setter_action_failed(self, p, monkeypatch):
        def x(**kwargs): # pylint:disable=unused-argument
            return ""

        monkeypatch.setattr(p.channel._ccu.api, "interface_set_value", x)

        with pytest.raises(PMActionFailed) as e:
            p.value = "false"
        assert "Failed to set" in str(e)

        assert p.set("false") == False


    def test_last_updated(self, p):
        p.datatype = "boolean" # fake for setting
        p.value = "true"

        last_updated = p.last_updated
        p.value = "true"
        assert last_updated < p.last_updated

        last_updated = p.last_updated
        p.value = "false"
        time.sleep(0.05)
        assert last_updated < p.last_updated


    def test_last_changed(self, p):
        p.datatype = "boolean" # fake for setting
        p.value = "true"

        last_changed = p.last_changed

        p.value = "true"
        assert last_changed == p.last_changed

        p.value = "false"
        time.sleep(0.05)
        assert last_changed < p.last_changed


    def test_is_visible_to_user(self, p):
        orig_flags = p.flags

        assert p.is_visible_to_user == True

        p.flags = 0
        assert p.is_visible_to_user == False

        p.flags = 3
        assert p.is_visible_to_user == True

        p.flags = 16
        assert p.is_visible_to_user == False

        p.flags = orig_flags


    def test_is_internal(self, p):
        orig_flags = p.flags

        assert p.is_internal == False

        p.flags = 2
        assert p.is_internal == True

        p.flags = 16
        assert p.is_internal == False

        p.flags = orig_flags


    def test_is_transformer(self, p):
        orig_flags = p.flags

        assert p.is_transformer == False

        p.flags = 4
        assert p.is_transformer == True

        p.flags = 9
        assert p.is_transformer == False

        p.flags = orig_flags


    def test_is_service(self, p):
        orig_flags = p.flags

        assert p.is_service == False

        p.flags = 8
        assert p.is_service == True

        p.flags = 16
        assert p.is_service == False

        p.flags = orig_flags


    def test_is_service_sticky(self, p):
        orig_flags = p.flags

        assert p.is_service_sticky == False

        p.flags = 16
        assert p.is_service_sticky == True

        p.flags = 12
        assert p.is_service_sticky == False

        p.flags = orig_flags


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
        if utils.is_py2():
            assert utils.is_byte_string(p.__str__())
            assert utils.is_text(p.__unicode__())
        else:
            assert utils.is_text(p.__str__())
            assert utils.is_byte_string(p.__bytes__())

        assert str(p) == "0"
        assert bytes(p) == b"0"


    def test_get_callbacks(self, p):
        assert p._get_callbacks("value_updated") == []
        assert p._get_callbacks("value_changed") == []

        with pytest.raises(PMException) as e:
            assert p._get_callbacks("hauruck")
        assert "Invalid callback" in str(e)


    def test_remove_callback(self, p):
        test = lambda: None

        # Don't raise when not registered yet
        p.remove_callback("value_updated", test)
        assert p._get_callbacks("value_updated") == []

        p.register_callback("value_updated", test)
        assert test in p._get_callbacks("value_updated")

        p.remove_callback("value_updated", test)
        assert p._get_callbacks("value_updated") == []



class TestParameterFLOAT(lib.TestCCUClassWide):
    @pytest.fixture(scope="function")
    def p(self, ccu):
        clima_regulator = list(ccu.devices.query(device_name="Bad-Thermostat"))[0].channels[2]
        return clima_regulator.values["SETPOINT"]


    def test_attributes(self, p):
        assert isinstance(p, ParameterFLOAT)
        assert p.type == "FLOAT"
        assert p.unit == u"°C"
        assert p.internal_name == "SETPOINT"
        assert p.name == "Setpoint"
        assert isinstance(p.value, float)
        assert isinstance(p.min, float)
        assert isinstance(p.max, float)
        assert isinstance(p.default, float)


    def test_from_api_value(self, p):
        assert p._from_api_value("0.00000000") == 0.0
        assert p._from_api_value("1.00000001") == 1.00000001
        assert p._from_api_value("1") == 1.0


    def test_to_api_value(self, p):
        assert p._to_api_value(1.0) == "1.000000"
        assert p._to_api_value(1.001) == "1.001000"
        assert p._to_api_value(999.124) == "999.124000"
        assert p._to_api_value(999.1240123) == "999.124012"


    def test_validate(self, p):
        assert p._validate(10.0) == True
        assert p._validate(10) == True
        with pytest.raises(PMException):
            p._validate(None)
        with pytest.raises(PMException):
            p._validate(p.min-1)
        with pytest.raises(PMException):
            p._validate(p.max+1)


    def test_formated(self, p):
        p._value = 1.0
        assert p.formated() == u"1.00 °C"
        p._value = 1.991
        assert p.formated() == u"1.99 °C"
        p._value = -1.991
        assert p.formated() == u"-1.99 °C"



class TestParameterBOOL(lib.TestCCUClassWide):
    @pytest.fixture(scope="function")
    def p(self, ccu):
        switch_state_channel = list(ccu.devices.query(device_name="Büro-Lampe"))[0].channels[1]
        return switch_state_channel.values["STATE"]


    def test_attributes(self, p):
        assert isinstance(p, ParameterBOOL)
        assert p.type == "BOOL"
        assert p.unit == ""
        assert p.internal_name == "STATE"
        assert p.name == "State"
        assert isinstance(p.value, bool)


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



class TestParameterACTION(TestParameterBOOL):
    @pytest.fixture(scope="function")
    def p(self, ccu):
        button0 = list(ccu.devices.query(device_name="Büro-Schalter"))[0].switch1
        assert isinstance(button0, ChannelKey)
        return button0.values["PRESS_SHORT"]


    def test_attributes(self, p):
        assert isinstance(p, ParameterACTION)
        assert p.type == "ACTION"
        assert p.unit == ""
        assert p.internal_name == "PRESS_SHORT"
        assert p.name == "Press Short"


    def test_readable(self, p):
        assert p.readable == False


    def test_get_value(self, p):
        with pytest.raises(PMException) as e:
            assert p.value != None
        assert "can not be read." in str(e)


    def test_last_updated(self, p):
        with pytest.raises(PMException) as e:
            assert p.last_updated != None
        assert "can not be read." in str(e)


    def test_last_changed(self, p):
        with pytest.raises(PMException) as e:
            assert p.last_changed != None
        assert "can not be read." in str(e)


    def test_set(self, p):
        p.value = True
        assert p.set(True)
        with pytest.raises(PMException):
            p.set(None)
        with pytest.raises(PMException):
            p.value = "1"
        with pytest.raises(PMException):
            p.value = None



class TestParameterINTEGER(lib.TestCCUClassWide):
    @pytest.fixture(scope="function")
    def p(self, ccu):
        clima_vent_drive = list(ccu.devices.query(device_name="Wohnzimmer"))[0].channels[4]
        return clima_vent_drive.values["BOOST_STATE"]


    def test_attributes(self, p):
        assert type(p) == ParameterINTEGER
        assert p.type == "INTEGER"
        assert p.unit == "min"
        assert p.internal_name == "BOOST_STATE"
        assert p.name == "Boost State"
        assert isinstance(p.value, int)
        assert isinstance(p.min, int)
        assert isinstance(p.max, int)
        assert isinstance(p.default, int)


    def test_from_api_value(self, p):
        assert p._from_api_value("1") == 1
        with pytest.raises(ValueError):
            p._from_api_value("1.0")


    def test_to_api_value(self, p):
        assert p._to_api_value(1) == "1"
        assert p._to_api_value(1.001) == "1"
        assert p._to_api_value(999) == "999"
        assert p._to_api_value(-999) == "-999"


    def test_validate(self, p):
        assert p._validate(p.min+1) == True
        assert p._validate(p.min) == True
        assert p._validate(p.max) == True

        with pytest.raises(PMException):
            p._validate(1.0)
        with pytest.raises(PMException):
            p._validate(None)
        with pytest.raises(PMException):
            p._validate(p.min-1)
        with pytest.raises(PMException):
            p._validate(p.max+1)


    def test_formated(self, p):
        p._value = 1
        assert p.formated() == "1 min"
        p._value = 101
        assert p.formated() == "101 min"
        p._value = -100
        assert p.formated() == "-100 min"



class TestParameterENUM(lib.TestCCUClassWide):
    @pytest.fixture(scope="function")
    def p(self, ccu):
        clima_vent_drive = list(ccu.devices.query(device_name="Bad-Heizung"))[0].channels[1]
        return clima_vent_drive.values["ERROR"]

    def test_attributes(self, p):
        assert isinstance(p, ParameterENUM)
        assert p.type == "ENUM"
        assert p.unit == ""
        assert p.internal_name == "ERROR"
        assert p.name == "Error"
        assert isinstance(p.value, int)
        assert isinstance(p.min, int)
        assert isinstance(p.max, int)
        assert isinstance(p.default, int)
        assert isinstance(p.value_list, list)


    def test_possible_values(self, p):
        assert isinstance(p.possible_values, list)


    def test_formated(self, p):
        assert utils.is_text(p.formated())
        assert p.formated() in p.possible_values



class TestParameterSTRING(lib.TestCCUClassWide):
    @pytest.fixture(scope="function")
    def p(self, ccu):
        trans = list(ccu.devices.query(device_name="Schlafzimmer-Links-Heizung"))[0].channels[4]
        return trans.values["PARTY_MODE_SUBMIT"]

    def test_attributes(self, p):
        assert isinstance(p, ParameterSTRING)
        assert p.type == "STRING"
        assert p.unit == ""
        assert p.internal_name == "PARTY_MODE_SUBMIT"
        assert p.name == "Party Mode Submit"
        assert utils.is_text(p.min)
        assert utils.is_text(p.max)
        assert utils.is_text(p.default)
