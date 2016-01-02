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

import pytest

from TestAPI import TestAPI
from pmatic.entities import *

class TestEntity:
    @pytest.fixture(scope="class")
    def API(self):
        return TestAPI()

    def test_minimal_entity(self, API):
        obj = Entity(API, {})

    def test_attributes(self, API):
        obj = Entity(API, {
            'ding_dong': 1,
            'BLA': 'blub', # keys are converted to lower case
            'blaBlubKey': 'XXX', # camel case conversion
        })

        assert obj.ding_dong == 1
        assert obj.bla == 'blub'
        assert obj.bla_blub_key == 'XXX'
        assert not hasattr(obj, "blaBlubKey")

    def test_attribute_conversion(self, API):
        def transform_with_api_obj(api_obj, val):
            assert type(api_obj) == TestAPI
            return val

        class TestEntity(Entity):
            transform_attributes = {
                "ding_dong"       : (False, int),
                "ding_dong_float" : (False, float),
                "BLA"             : (True,  transform_with_api_obj),
            }

        obj = TestEntity(API, {
            'ding_dong': "1",
            'ding_dong_float': "1.0",
            'BLA': 'blub',
            'blah': 'blux',
        })

        assert obj.ding_dong == 1
        assert obj.ding_dong_float == 1.0
        assert obj.bla == "blub"
        assert obj.blah == "blux"


def test_device_class_list():
    assert len(device_classes_by_type_name) > 0
    assert "Device" not in device_classes_by_type_name
    assert "SpecificDevice" not in device_classes_by_type_name
    assert "HM-ES-PMSw1-Pl" in device_classes_by_type_name
    assert device_classes_by_type_name["HM-ES-PMSw1-Pl"] == HMESPMSw1Pl


def test_channel_class_list():
    assert len(channel_classes_by_type_name) > 0
    assert "Channel" not in channel_classes_by_type_name
    assert "CLIMATECONTROL_REGULATOR" in channel_classes_by_type_name
    assert channel_classes_by_type_name["CLIMATECONTROL_REGULATOR"] == ChannelClimaRegulator
