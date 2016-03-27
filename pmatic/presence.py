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

import pmatic.utils as utils
from pmatic.exceptions import PMUserError, PMException


try:
    from simpletr64.actions.lan import Lan as SimpleTR64Lan
except ImportError as e:
    if "simpletr64" in str(e):
        SimpleTR64Lan = None
    else:
        raise


class Presence(object):
    """This class is meant to detect presence of persons. It is using
    a modularized collection of possible plugins which can be used
    to detect the presence. For example there is one plugin to detect
    the presence of users by asking a local fritz!Box for the current
    active devices. The devices are then matched with the configuration
    of persons."""
    def __init__(self):
        super(Presence, self).__init__()
        self.persons = []


    def from_config(self, cfg):
        """Build the presence object, persons and devices from a persisted
        configuration dictionary."""
        self.persons = []

        for person_cfg in cfg.get("persons", []):
            p = Person(self)
            p.from_config(person_cfg)
            self.add_person(p)


    def to_config(self):
        """Returns a dictionary representing the whole presence configuration.
        This dictionary can be saved somewhere, for example in a file, loaded
        afterwards and handed over to :meth:`from_config` to reconstruct the
        current presence object."""
        return {
            "persons": [ p.to_config() for p in self.persons ],
        }


    def update(self):
        """Call this to update the presence information of all configured persons
        and their devices. This normally calls the presence plugins to update the
        presence information from the connected data source."""
        for person in self.persons:
            person.update_presence()


    def add_person(self, p):
        """Add a :class:`Person` object to the presence detection."""
        self.persons.append(p)



class Person(utils.LogMixin):
    def __init__(self, presence):
        super(Person, self).__init__()
        self._presence = presence
        self.name      = "Mr. X"
        self.devices   = []

        self._presence_updated = None
        self._presence_changed = None
        self._present          = False


    def from_config(self, cfg):
        self.name = cfg["name"]

        self.devices = []
        for device_cfg in cfg.get("devices", []):
            cls = PersonalDevice.get(device_cfg["type_name"])
            if not cls:
                raise PMUserError("Failed to load personal device type: %s" %
                                                            device_cfg["type_name"])

            device = cls()
            device.from_config(device_cfg)
            self.add_device(device)


    def to_config(self):
        return {
            "name"    : self.name,
            "devices" : [ d.to_config() for d in self.devices ],
        }


    @property
    def present(self):
        """Is ``True`` when the user is present and ``False`` when not."""
        return self._present


    def add_device(self, device):
        """Adds a :class:`PersonalDevice` object to the person. Please note that
        you need to use a specific class inherited from :class:`PersonalDevice`,
        for example the :class:`PersonalDeviceFritzBoxHost` class."""
        self.devices.append(device)


    def update_presence(self):
        """Updates the presence of this person. When at least one device is active,
        the person is treated to be present."""
        if not self.devices:
            self.logger.debug("Has no devices associated. Not updating the presence.")
            return

        new_value = False
        for device in self.devices:
            if device.active:
                new_value = True
                break

        self._set_presence(new_value)


    def _set_presence(self, new_value):
        """Internal helper for setting the presence state"""
        old_value = self._present

        now = time.time()
        self._presence_updated = now

        self._present = new_value
        if new_value != old_value:
            self._presence_changed = True



class PersonalDevice(object):
    type_name  = ""
    type_title = ""

    @classmethod
    def types(cls):
        """Returns a list of all available specific PersonalDevice classes"""
        return cls.__subclasses__()


    @classmethod
    def get(cls, type_name):
        """Returns the subclass of PersonalDevice which matches the given :attr:`type_name`
        or ``None`` if there is no match."""
        for subclass in cls.__subclasses__():
            if subclass.type_name == type_name:
                return subclass
        return None


    def __init__(self):
        super(PersonalDevice, self).__init__()
        self._name   = "Unspecific device"
        self._active = False


    def from_config(self, cfg):
        for key, val in cfg.items():
            setattr(self, "_" + key, val)


    def to_config(self):
        return {
            "type_name": self.type_name,
        }


    @property
    def name(self):
        """Provides the name of this device."""
        return self._name


    @property
    def active(self):
        """Whether or not this device is currently active."""
        return self._active



class PersonalDeviceFritzBoxHost(PersonalDevice):
    type_name = "fritz_box_host"
    type_title = "fritz!Box Host"

    # Class wide connection handling (not per object)
    connection = None
    _address   = None
    _port      = None
    _user      = None
    _password  = None

    @classmethod
    def configure(cls, address, protocol=None, port=None, user=None, password=None):
        cls._address    = address or "fritz.box"
        cls._protocol   = protocol or "http"
        cls._port       = port or 49000
        cls._user       = user or ""
        cls._password   = password or ""


    @classmethod
    def _connect(cls):
        if SimpleTR64Lan == None:
            raise PMException("Could not import the required \"simpletr64.actions.lan.Lan\".")

        if cls.connection == None:
            cls.connection = SimpleTR64Lan(hostname=cls._address,
                                           port=cls._port,
                                           protocol=cls._protocol)
            cls.connection.setupTR64Device("fritz.box")
            cls.connection.username = cls._user
            cls.connection.password = cls._password


    def __init__(self):
        super(PersonalDeviceFritzBoxHost, self).__init__()
        self._name       = "fritz!Box Device"
        self._ip_address = None


    def _update_host_info(self):
        PersonalDeviceFritzBoxHost._connect()
        try:
            result = PersonalDeviceFritzBoxHost.connection.getHostDetailsByMACAddress(self._mac)
        except ValueError as e:
            # Is raised when no device with this mac can be found
            if "NoSuchEntryInArray" in str(e):
                return
            else:
                raise

        self._ip_address = result.ipaddress
        self._name       = result.hostname
        self._active     = result.active


    @property
    def name(self):
        """Provides the name of this device."""
        self._update_host_info()
        return self._name


    @property
    def active(self):
        """Whether or not this device is currently active."""
        self._update_host_info()
        return self._active
