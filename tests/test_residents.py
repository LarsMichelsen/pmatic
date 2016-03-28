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

import time
import pytest

from simpletr64.actions.lan import Lan, HostDetails

import pmatic.residents
from pmatic.residents import Residents, Resident, PersonalDevice, \
                            PersonalDeviceFritzBoxHost
from pmatic.exceptions import PMUserError, PMException


class TestResidents(object):
    @pytest.fixture(scope="function")
    def p(self):
        return Residents()


    def _add_resident(self, pr):
        pr.from_config({
            "residents": [
                {
                    "name": "Lars",
                    "email": "",
                    "mobile": "",
                    "pushover_token": "",
                    "devices" : [
                        {
                            "type_name": "fritz_box_host",
                            "mac": "30:10:E6:10:D4:B2",
                        },
                    ]
                }
            ],
        })


    def test_from_config(self, p):
        assert p.residents == []
        p.from_config({})
        assert p.residents == []

        self._add_resident(p)
        assert len(p.residents) == 1
        assert type(p.residents[0]) == Resident


    def test_to_config(self, p):
        assert p.to_config() == {"residents": []}

        self._add_resident(p)
        assert isinstance(p.to_config(), dict)
        assert len(p.to_config()) == 1


    def test_update(self, p):
        assert p.residents == []
        p.update()

        def x():
            raise PMException("TEST")

        self._add_resident(p)
        p.residents[0].update_presence = x
        with pytest.raises(PMException) as e:
            p.update()
        assert "TEST" in str(e)


    def test_add(self, p):
        assert p.residents == []
        p.add(Resident(p))
        assert len(p.residents) == 1
        assert isinstance(p.residents[0], Resident)


    def test_exists(self, p):
        assert p.residents == []
        assert p.exists(0) == False
        p.add(Resident(p))
        assert p.exists(0) == True
        assert p.exists(1) == False


    def test_get(self, p):
        assert p.residents == []
        with pytest.raises(IndexError):
            assert p.get(0)
        p.add(Resident(p))
        assert isinstance(p.get(0), Resident)
        with pytest.raises(IndexError):
            assert p.get(1)


    def test_get_by_name(self, p):
        assert p.residents == []
        assert p.get_by_name("Harry") == None
        self._add_resident(p)
        r = p.get_by_name("Lars")
        assert isinstance(r, Resident)
        assert r.name == "Lars"


    def test_remove(self, p):
        assert p.residents == []
        p.remove(0)
        self._add_resident(p)
        assert len(p.residents) == 1
        p.remove(0)
        assert p.residents == []


    def test_clear(self, p):
        self._add_resident(p)
        assert len(p.residents) == 1
        p.clear()
        assert p.residents == []



class TestResident(object):
    @pytest.fixture(scope="function")
    def p(self):
        residents = Residents()
        return Resident(residents)


    def test_init(self, p):
        assert p.name == "Mr. X"
        assert p.devices == []
        assert p.present == False
        assert p.last_updated == None
        assert p.last_changed == None


    def _from_config(self, resident):
        resident.from_config({
            "name": "Lars",
            "email": "",
            "mobile": "",
            "pushover_token": "",
            "devices" : [
                {
                    "type_name": "fritz_box_host",
                    "mac": "30:10:E6:10:D4:B2",
                },
            ]
        })


    def test_from_config(self, p):
        self._from_config(p)
        assert p.name == "Lars"
        assert len(p.devices) == 1
        assert isinstance(p.devices[0], PersonalDevice)

        with pytest.raises(PMUserError) as e:
            p.from_config({
                "name": "Lars",
                "email": "",
                "mobile": "",
                "pushover_token": "",
                "devices" : [
                    {
                        "type_name": "invalid_type",
                    },
                ]
            })
        assert "device type: invalid_type" in str(e)


    def test_to_config(self, p):
        assert isinstance(p.to_config(), dict)
        assert p.to_config()["name"] == p.name
        assert p.to_config()["devices"] == []

        self._from_config(p)
        assert isinstance(p.to_config()["devices"][0], dict)


    def test_present(self, p):
        assert p.present == False
        p._present = True
        assert p.present == True


    def test_add_device(self, p):
        assert p.devices == []
        p.add_device(PersonalDevice())
        assert len(p.devices) == 1


    def test_update_presence(self, p):
        assert p.devices == []
        p.update_presence() # Should not change anything

        self._from_config(p)
        p.devices[0]._active = False
        p.update_presence()
        assert p.present == False

        d = PersonalDevice()
        d._active = True
        p.add_device(d)
        p.update_presence()
        assert p.present == True


    def test_set_presence(self, p):
        assert p._present == False
        assert p.last_updated == None
        assert p.last_changed == None

        p._set_presence(False)
        assert p._present == False
        assert p.last_updated > time.time() - 60
        assert p.last_changed == None
        old_updated, old_changed = p._presence_updated, p._presence_changed

        p._set_presence(True)
        assert p._present == True
        assert p.last_updated >= old_updated
        assert p.last_changed > time.time() - 60
        assert p.last_changed == p.last_updated
        old_updated, old_changed = p._presence_updated, p._presence_changed

        p._set_presence(False)
        assert p._present == False
        assert p.last_updated > old_updated
        assert p.last_changed > old_changed
        assert p.last_changed == p.last_updated


    def test_clear_devices(self, p):
        self._from_config(p)
        assert len(p.devices) == 1
        p.clear_devices()
        assert p.devices == []



class TestPersonalDevice(object):
    def test_types(self):
        types = PersonalDevice.types()
        assert len(types) > 0


    def test_get(self):
        assert PersonalDevice.get("xyz") == None
        assert PersonalDevice.get("fritz_box_host") == PersonalDeviceFritzBoxHost


    @pytest.fixture(scope="function")
    def d(self):
        return PersonalDevice()


    def test_init(self, d):
        assert d.name == "Unspecific device"
        assert d.active == False


    def test_from_config(self, d):
        d.from_config({
            "name": "Harry"
        })
        assert d.name == "Harry"


    def test_to_config(self, d):
        assert d.to_config() == {"type_name": ""}
        d.type_name = "AAA"
        assert d.to_config() == {"type_name": "AAA"}



class TestPersonalDeviceFritzBoxHost(object):
    def test_cls(self):
        assert PersonalDeviceFritzBoxHost.type_name == "fritz_box_host"
        assert PersonalDeviceFritzBoxHost.type_title == "fritz!Box Host"

    def test_configure(self):
        assert PersonalDeviceFritzBoxHost._address  == "fritz.box"
        assert PersonalDeviceFritzBoxHost._protocol == "http"
        assert PersonalDeviceFritzBoxHost._port     == 49000
        assert PersonalDeviceFritzBoxHost._user     == ""
        assert PersonalDeviceFritzBoxHost._password == ""

        PersonalDeviceFritzBoxHost.configure("asd123")
        assert PersonalDeviceFritzBoxHost._address  == "asd123"
        assert PersonalDeviceFritzBoxHost._protocol == "http"

        PersonalDeviceFritzBoxHost.configure(protocol="https")
        assert PersonalDeviceFritzBoxHost._address  == "asd123"
        assert PersonalDeviceFritzBoxHost._protocol == "https"

        PersonalDeviceFritzBoxHost.configure("host", "proto", "port", "user", "pw")
        assert PersonalDeviceFritzBoxHost._address  == "host"
        assert PersonalDeviceFritzBoxHost._protocol == "proto"
        assert PersonalDeviceFritzBoxHost._port     == "port"
        assert PersonalDeviceFritzBoxHost._user     == "user"
        assert PersonalDeviceFritzBoxHost._password == "pw"


    def test_connect(self, monkeypatch):
        monkeypatch.setattr(pmatic.residents, "SimpleTR64Lan", None)
        with pytest.raises(PMException) as e:
            PersonalDeviceFritzBoxHost._connect()
        assert "simpletr64.actions.lan.Lan" in str(e)
        monkeypatch.undo()

        PersonalDeviceFritzBoxHost.connection = "X"
        PersonalDeviceFritzBoxHost._connect()
        assert PersonalDeviceFritzBoxHost.connection == "X"
        PersonalDeviceFritzBoxHost.connection = None

        PersonalDeviceFritzBoxHost._connect()
        assert isinstance(PersonalDeviceFritzBoxHost.connection, Lan)


    @pytest.fixture(scope="function")
    def f(self):
        d = PersonalDeviceFritzBoxHost()
        d.from_config({"mac": "00:de:ad:be:ef:00"})
        return d


    def test_init(self, f):
        assert f.name == "fritz!Box Device"
        assert f.active == False
        assert f._ip_address == None
        assert f._mac == "00:de:ad:be:ef:00"

    def _details_is_active(self, mac_address):
        return HostDetails({
            "NewMACAddress"    : mac_address,
            "NewHostName"      : "blafasel",
            "NewIPAddress"     : "123.123.123.123",
            "NewActive"        : "1",
            "NewInterfaceType" : None,
            "NewAddressSource" : None,
            "NewLeaseTimeRemaining" : 1,
        })


    def test_update_host_info(self, f, monkeypatch):
        def _details_is_inactive(mac_address):
            return HostDetails({
                "NewMACAddress"    : mac_address,
                "NewHostName"      : "blafaselgnah",
                "NewIPAddress"     : "123.123.123.123",
                "NewActive"        : "0",
                "NewInterfaceType" : None,
                "NewAddressSource" : None,
                "NewLeaseTimeRemaining" : 1,
            })

        def _details_invalid_mac(mac_address):
            raise ValueError("Could note execute ... bla ... -- NoSuchEntryInArray")

        def _details_another_error(mac_address):
            raise ValueError("Could note execute ... bla ... -- irgendwas")

        monkeypatch.setattr(PersonalDeviceFritzBoxHost.connection, "getHostDetailsByMACAddress",
                            self._details_is_active)

        f._update_host_info()
        assert f.name == "blafasel"
        assert f.active == True

        monkeypatch.setattr(PersonalDeviceFritzBoxHost.connection, "getHostDetailsByMACAddress",
                            _details_is_inactive)

        f._update_host_info()
        assert f.name == "blafaselgnah"
        assert f.active == False

        monkeypatch.setattr(PersonalDeviceFritzBoxHost.connection, "getHostDetailsByMACAddress",
                            _details_invalid_mac)

        f._update_host_info()
        assert f.name == "blafaselgnah"
        assert f.active == False

        monkeypatch.setattr(PersonalDeviceFritzBoxHost.connection, "getHostDetailsByMACAddress",
                            _details_another_error)

        with pytest.raises(ValueError):
            f._update_host_info()
        assert f.name == "blafaselgnah"
        assert f.active == False


    def test_name(self, f, monkeypatch):
        assert f.name != "blafasel"
        monkeypatch.setattr(PersonalDeviceFritzBoxHost.connection, "getHostDetailsByMACAddress",
                            self._details_is_active)
        f._update_host_info()
        assert f.name == "blafasel"


    def test_active(self, f, monkeypatch):
        assert f._active == False
        monkeypatch.setattr(PersonalDeviceFritzBoxHost.connection, "getHostDetailsByMACAddress",
                            self._details_is_active)
        f._update_host_info()
        assert f.active == True
