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

import pmatic.api
import pmatic.utils as utils
from test_api_remote import TestRemoteAPI
from pmatic.entities import Entity, Channel, Device, Devices, HMESPMSw1Pl, ChannelClimaRegulator, \
                            device_classes_by_type_name, channel_classes_by_type_name

class TestEntity(TestRemoteAPI):
    def test_minimal_entity(self, API):
        Entity(API, {})

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
        def transform_with_api_obj(api, val):
            assert type(api) == pmatic.api.RemoteAPI
            return val

        class TestEntity(Entity):
            transform_attributes = {
                "ding_dong"       : int,
                "ding_dong_float" : float,
                "BLA"             : transform_with_api_obj,
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



class TestDevices(TestRemoteAPI):
    @pytest.fixture()
    def devices(self, API):
        return Devices(API)

    def test_init(self, API):
        Devices(API)
        #with pytest.raises():
        Devices(None)


    def test_get_all(self, API, devices):
        assert list(devices) == []

        devices.get()
        assert len(devices) > 0


    def test_get_multiple(self, API, devices):
        result1 = devices.get(device_type="HM-ES-PMSw1-Pl")
        assert len(result1) > 0

        assert devices != result1

        result2 = devices.get(device_type="xxx")
        assert len(result2) == 0

        result3 = devices.get(device_type="HM-CC-RT-DN")
        assert len(result3) > 0

        assert len(devices) == len(result1) + len(result3)


    def test_create_from_low_level_dict(self, API, devices):
        device1 = list(pmatic.api.DeviceSpecs(API).values())[0]
        device = devices._create_from_low_level_dict(device1)

        assert isinstance(device, Device)
        assert device.address == device1["address"]
        assert utils.is_text(device.name)
        assert device.name != ""


    def test_add_from_low_level_dict(self, API, devices):
        device1 = list(pmatic.api.DeviceSpecs(API).values())[0]
        devices.add_from_low_level_dict(device1)
        assert len(devices) == 1


    def test_add(self, API, devices):
        device1_spec = list(pmatic.api.DeviceSpecs(API).values())[0]
        device = Device.from_dict(API, device1_spec)

        devices.add(device)
        assert len(devices) == 1


    def test_exists(self, API, devices):
        device1_spec = list(pmatic.api.DeviceSpecs(API).values())[0]
        device = Device.from_dict(API, device1_spec)

        assert not devices.exists(device.address)
        devices.add(device)
        assert devices.exists(device.address)
        assert not devices.exists(device.address+"x")


    def test_addresses(self, API, devices):
        device1 = list(pmatic.api.DeviceSpecs(API).values())[0]
        devices.add_from_low_level_dict(device1)

        if utils.is_py2():
            assert type(devices.addresses()) == list
        else:
            assert type(list(devices.addresses())) == list

        assert len(devices.addresses()) == 1
        if utils.is_py2():
            assert devices.addresses() == [device1["address"]]
        else:
            assert list(devices.addresses()) == [device1["address"]]


    def test_delete(self, API, devices):
        device1 = list(pmatic.api.DeviceSpecs(API).values())[0]
        devices.add_from_low_level_dict(device1)

        assert len(devices) == 1
        devices.delete(device1["address"])
        assert len(devices) == 0

        devices.delete("xxx123")


    def test_clear(self, API, devices):
        assert len(devices) == 0
        devices.clear()
        assert len(devices) == 0
        device1 = list(pmatic.api.DeviceSpecs(API).values())[0]
        devices.add_from_low_level_dict(device1)

        assert len(devices) == 1
        devices.clear()
        assert len(devices) == 0


    def get_device_or_channel_by_address(self, API, devices):
        device1 = list(pmatic.api.DeviceSpecs(API).values())[0]
        devices.add_from_low_level_dict(device1)

        dev = devices.device_or_channel_by_address(device1["address"])
        assert isinstance(dev, Device)
        assert dev.address == device1["address"]

        chan = devices.device_or_channel_by_address(device1["address"]+":1")
        assert isinstance(chan, Channel)
        assert dev.address != device1["address"]

        with pytest.raises("KeyError"):
            devices.device_or_channel_by_address(device1["address"]+":99")

        with pytest.raises("KeyError"):
            devices.device_or_channel_by_address("xxxxxxx")



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
