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
import lib
from pmatic.entities import Entity, Channel, Device, Devices, HMESPMSw1Pl, ChannelClimaRegulator, \
                            device_classes_by_type_name, channel_classes_by_type_name
from pmatic.ccu import CCUDevices
from pmatic.exceptions import PMException

class TestEntity(lib.TestCCU):
    def test_minimal_entity(self, ccu):
        Entity(ccu, {})

    def test_attributes(self, ccu):
        obj = Entity(ccu, {
            'ding_dong': 1,
            'BLA': 'blub', # keys are converted to lower case
            'blaBlubKey': 'XXX', # camel case conversion
        })

        assert obj.ding_dong == 1
        assert obj.bla == 'blub'
        assert obj.bla_blub_key == 'XXX'
        assert not hasattr(obj, "blaBlubKey")

    def test_attribute_conversion(self, ccu):
        def transform_with_ccu_obj(ccu, val):
            assert isinstance(ccu, pmatic.CCU)
            return val

        def transform_with_api_obj(api, val):
            assert isinstance(api, pmatic.api.RemoteAPI)
            return val

        def transform_with_device_obj(device, val):
            assert isinstance(device, Device)
            return val

        def transform_with_object_obj(obj, val):
            assert isinstance(obj, Entity)
            return val

        class TestDevice(Device):
            _transform_attributes = {
                "ding_dong"       : int,
                "ding_dong_float" : float,
                "XXX"             : transform_with_ccu_obj,
                "BLA"             : transform_with_api_obj,
                "BLUB"            : transform_with_device_obj,
                "HUH"             : transform_with_object_obj,
            }
            _mandatory_attributes = []

        obj = TestDevice(ccu, {
            'ding_dong': "1",
            'ding_dong_float': "1.0",
            'BLA': 'blub',
            'BLUB': 'dingeling',
            'HUH': 'hasbasl',
            'blah': 'blux',
        })

        assert obj.ding_dong == 1
        assert obj.ding_dong_float == 1.0
        assert obj.bla == "blub"
        assert obj.blub == "dingeling"
        assert obj.huh == "hasbasl"
        assert obj.blah == "blux"


    def test_mandatory_attributes(self, ccu):
        class TestEntity(Entity):
            _mandatory_attributes = [
                "dasda",
            ]

        obj = TestEntity(ccu, {
            'ding_dong': "1",
            'dasda': 'paff',
            'blah': 'blux',
        })

        assert obj.ding_dong == "1"
        assert obj.dasda == "paff"
        assert obj.blah == "blux"

        with pytest.raises(PMException) as e:
            TestEntity(ccu, {
                'ding_dong': "1",
                'blah': 'blux',
            })
        assert "mandatory attribute" in str(e)



class TestChannel(lib.TestCCU):
    #@pytest.fixture(scope="class")
    #def channel(self, API):
    #    device = Device(API, {
    #        'address': 'KEQ0970393',
    #        #'children': ['KEQ0970393:0',
    #        #             'KEQ0970393:1',
    #        #             'KEQ0970393:2',
    #        #             'KEQ0970393:3',
    #        #             'KEQ0970393:4',
    #        #             'KEQ0970393:5',
    #        #             'KEQ0970393:6',
    #        'firmware': '1.4',
    #        'flags': 1,
    #        'interface': 'KEQ0714972',
    #        #'paramsets': ['MASTER'],
    #        'roaming': False,
    #        'type': 'HM-ES-PMSw1-Pl',
    #        'updatable': '1',
    #        'version': 1,
    #        'channels': [],
    #    })

    #    return Channel(device, {
    #        'address': 'KEQ0970393:1',
    #        'direction': 1,
    #        'flags': 1,
    #        'index': 1,
    #        'link_source_roles': [
    #            'KEYMATIC',
    #            'SWITCH',
    #            'WINDOW_SWITCH_RECEIVER',
    #            'WINMATIC'
    #        ],
    #        'link_target_roles': [],
    #        'paramsets': ['LINK', 'MASTER', 'VALUES'],
    #        'type': 'SHUTTER_CONTACT',
    #        'version': 15,
    #    })


    def test_channel_invalid_device(self):
        with pytest.raises(PMException) as e:
            Channel(None, {})
        assert "not a Device derived" in str(e)


    def test_channel_unknown_type(self, capfd, ccu):
        # Set loglevel so that we get the debug message
        pmatic.logging(pmatic.DEBUG)

        device = Device(ccu, {
            'address': 'KEQ0970393',
            'firmware': '1.4',
            'flags': 1,
            'interface': 'KEQ0714972',
            'roaming': False,
            'type': 'HM-ES-PMSw1-Pl',
            'updatable': '1',
            'version': 1,
            'channels': [],
        })

        Channel.from_channel_dicts(device, [
            {
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
                'type': 'XXX_SHUTTER_CONTACT',
                'version': 15,
            }
        ])

        out, err = capfd.readouterr()
        assert "Using generic" in err
        assert "XXX_SHUTTER_CONTACT" in err
        assert out == ""

        # revert to default log level
        pmatic.logging()


    def test_summary_state(self, ccu):
        device = list(ccu.devices.query(device_type="HM-ES-PMSw1-Pl"))[0]
        assert device.summary_state != ""
        assert utils.is_text(device.summary_state)



class TestDevices(lib.TestCCU):
    @pytest.fixture(scope="function")
    def devices(self, ccu):
        return Devices(ccu)

    def test_init(self, ccu):
        Devices(ccu)
        with pytest.raises(PMException):
            Devices(None)


    def test_get_all(self, ccu, devices):
        assert list(devices) == []
        assert len(devices) == 0
        assert isinstance(devices._device_dict, dict)
        assert len(devices._device_dict) == 0

        result1 = ccu.devices.query(device_type="HM-ES-PMSw1-Pl")
        devices.add(list(result1)[0])
        assert len(devices) == 1
        assert len(devices._device_dict) == 1


    def test_add(self, ccu, devices):
        device1 = list(ccu.devices)[0]

        if isinstance(self, TestCCUDevices):
            ccu.devices.delete(device1.address)
            expected_len = len(ccu.devices)+1
        else:
            expected_len = 1

        devices.add(device1)
        assert len(devices) == expected_len

        with pytest.raises(PMException):
            devices.add(None)

        assert len(devices) == expected_len


    def test_exists(self, ccu, devices):
        device = list(ccu.devices)[0]
        assert not devices.exists(device.address)
        devices.add(device)
        assert devices.exists(device.address)
        assert not devices.exists(device.address+"x")


    def test_addresses(self, ccu, devices):
        device1 = list(ccu.devices)[0]
        devices.add(device1)

        if utils.is_py2():
            assert isinstance(devices.addresses(), list)
        else:
            assert isinstance(list(devices.addresses()), list)

        assert len(devices.addresses()) == 1
        if utils.is_py2():
            assert devices.addresses() == [device1.address]
        else:
            assert list(devices.addresses()) == [device1.address]


    def test_delete(self, ccu, devices):
        device1 = list(ccu.devices)[0]
        devices.add(device1)

        assert len(devices) == 1
        devices.delete(device1.address)
        assert len(devices) == 0

        devices.delete("xxx123")


    def test_clear(self, ccu, devices):
        assert len(devices) == 0
        devices.clear()
        assert len(devices) == 0

        device1 = list(ccu.devices)[0]
        devices.add(device1)

        assert len(devices) == 1
        devices.clear()
        assert len(devices) == 0


    def test_get_device_or_channel_by_address(self, ccu, devices):
        device1 = list(ccu.devices)[0]
        devices.add(device1)

        dev = devices.get_device_or_channel_by_address(device1.address)
        assert isinstance(dev, Device)
        assert dev.address == device1.address

        chan = devices.get_device_or_channel_by_address(device1.address+":1")
        assert isinstance(chan, Channel)
        assert chan.address != device1.address

        with pytest.raises(KeyError):
            devices.get_device_or_channel_by_address(device1.address+":99")

        with pytest.raises(KeyError):
            devices.get_device_or_channel_by_address("xxxxxxx")



class TestCCUDevices(TestDevices):
    @pytest.fixture(scope="function")
    def devices(self, ccu):
        return CCUDevices(ccu)


    def test_ccu_devices_wrong_init(self):
        with pytest.raises(PMException):
            return CCUDevices(None)


    def test_get_all(self, ccu, devices):
        assert len(devices._device_dict) == 0
        assert list(devices) != []
        all_len = len(devices)
        assert all_len > 0
        assert isinstance(devices._device_dict, dict)
        assert len(devices._device_dict) > 0

        result1 = ccu.devices.query(device_type="HM-ES-PMSw1-Pl")
        devices.add(list(result1)[0])
        assert len(devices) == all_len


    def test_query(self, ccu):
        assert len(ccu.devices._device_dict) == 0

        result1 = ccu.devices.query(device_type="HM-ES-PMSw1-Pl")
        assert len(result1) > 0

        assert len(ccu.devices._device_dict) == len(result1)

        result2 = ccu.devices.query(device_type="xxx")
        assert len(result2) == 0

        result3 = ccu.devices.query(device_type="HM-CC-RT-DN")
        assert len(result3) > 0

        result4 = ccu.devices.query(device_name_regex="^%$")
        assert len(result4) == 0

        result5 = ccu.devices.query(device_name_regex="^Schlafzimmer.*$")
        assert len(result5) > 0

        result6 = ccu.devices.query(device_address="")
        assert len(result6) == 0

        result7 = ccu.devices.query(device_address="KEQ0970393")
        assert len(result7) > 0

        all_returned = list(set(list(result1) + list(result3) + list(result5) + list(result7)))

        assert len(ccu.devices._device_dict) == len(all_returned)


    def test_create_from_low_level_dict(self, API, devices):
        device1 = list(pmatic.api.DeviceSpecs(API).values())[0]
        device = devices._create_from_low_level_dict(device1)

        assert isinstance(device, Device)
        assert device.address == device1["address"]
        assert utils.is_text(device.name)
        assert device.name != ""


    def test_add_from_low_level_dict(self, API, devices):
        device1_dict = list(pmatic.api.DeviceSpecs(API).values())[0]
        expected_len = len(devices)

        devices.delete(device1_dict["address"])
        assert len(devices) == expected_len-1

        devices.add_from_low_level_dict(device1_dict)
        assert len(devices) == expected_len


    def test_exists(self, ccu, devices):
        device = list(ccu.devices)[0]
        assert devices.exists(device.address)
        devices.delete(device.address)
        assert not devices.exists(device.address)
        assert not devices.exists(device.address+"x")


    def test_addresses(self, ccu, devices):
        if utils.is_py2():
            assert isinstance(devices.addresses(), list)
        else:
            assert isinstance(list(devices.addresses()), list)

        assert len(devices.addresses()) > 0

        for address in devices.addresses():
            assert len(address) == 10 or address == "BidCoS-RF"


    def test_delete(self, ccu, devices):
        device1 = list(ccu.devices)[0]
        expected_len = len(devices)-1

        devices.delete(device1.address)
        assert len(devices) == expected_len

        devices.delete("xxx123")
        assert len(devices) == expected_len


    def test_clear(self, ccu, devices):
        assert len(devices._device_dict) == 0
        assert len(devices) > 0
        devices.clear()
        assert len(devices._device_dict) == 0


    def test_get_device_or_channel_by_address(self, ccu, devices):
        device1 = list(ccu.devices)[0]
        devices.add(device1)

        dev = devices.get_device_or_channel_by_address(device1.address)
        assert isinstance(dev, Device)
        assert dev.address == device1.address

        chan = devices.get_device_or_channel_by_address(device1.address+":1")
        assert isinstance(chan, Channel)
        assert chan.address != device1.address

        with pytest.raises(KeyError):
            devices.get_device_or_channel_by_address(device1.address+":99")

        with pytest.raises(KeyError):
            devices.get_device_or_channel_by_address("xxxxxxx")


    def test_already_initialized_devices(self, ccu):
        assert len(ccu.devices.already_initialized_devices) == 0

        result1 = ccu.devices.query(device_type="HM-ES-PMSw1-Pl")
        assert len(result1) > 0

        assert len(ccu.devices.already_initialized_devices) == len(result1)



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
