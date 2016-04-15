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

import re
import time
import requests.exceptions

import pmatic.utils as utils
from pmatic.exceptions import PMUserError, PMException

try:
    from simpletr64.actions.lan import Lan as SimpleTR64Lan
except ImportError as e:
    if "simpletr64" in str(e):
        SimpleTR64Lan = None
    else:
        raise


class Residents(utils.LogMixin):
    """This class is meant to manage your residents and the presence of them."""
    def __init__(self):
        super(Residents, self).__init__()
        self._next_resident_id = 0
        self.residents = []


    def from_config(self, cfg):
        """Build the Residents object, residents and devices from a persisted
        configuration dictionary."""
        self.clear()

        self._next_resident_id = cfg.get("next_resident_id", 0)
        for resident_cfg in cfg.get("residents", []):
            r = Resident(self)
            r.from_config(resident_cfg)
            self._add(r)


    def to_config(self):
        """Returns a dictionary representing the whole residents configuration.
        This dictionary can be saved somewhere, for example in a file, loaded
        afterwards and handed over to :meth:`from_config` to reconstruct the
        current Residents object."""
        return {
            "next_resident_id" : self._next_resident_id,
            "residents"        : [ p.to_config() for p in self.residents ],
        }


    def from_state(self, state):
        """Updates the variable state data which can change during runtime on the
        current resident object."""
        for resident, resident_state in zip(self.residents, state):
            resident.from_state(resident_state)


    def to_state(self):
        """Returns a list of resident states. Each entry represents the state of
        a configured resident gathered with :meth:`Resident.to_state`."""
        return [ r.to_state() for r in self.residents ]


    @property
    def enabled(self):
        """Is set to ``True`` when the presence detection shal be enabled."""
        return bool(self.residents)


    def update(self):
        """Call this to update the presence information of all configured residents
        and their devices. This normally calls the presence plugins to update the
        presence information from the connected data source."""
        self.logger.debug("Updating presence information")
        for resident in self.residents:
            resident.update_presence()


    def add(self, r):
        """Add a :class:`Resident` object to the collection. This method automatically
        generates a new resident id for the object and stores this key within the object.
        """
        r.id = self._next_resident_id
        self._next_resident_id += 1
        self._add(r)


    def _add(self, r):
        """Internal helper to add the given resident to this collection."""
        self.residents.append(r)


    def exists(self, resident_id):
        """Returns ``True`` when a resident with the given id exists.
        Otherwise ``False`` is returned."""
        return self.get(resident_id) != None


    def get(self, resident_id):
        """Returns the :class:`Resident` matching the given ``resident_id``. Returns None
        when this resident does not exist."""
        for resident in self.residents:
            if resident.id == resident_id:
                return resident


    def get_by_name(self, resident_name):
        """Returns the first :class:`Resident` matching the given ``resident_name``. Returns
        ``None`` when there is no resident with this name."""
        for resident in self.residents:
            if resident.name == resident_name:
                return resident
        return None


    def remove(self, resident_id):
        """Removes the resident with the given ``resident_id`` from the Residents. Tolerates non
        existing resident ids."""
        for resident in self.residents:
            if resident.id == resident_id:
                self.residents.remove(resident)
                return


    def clear(self):
        """Resets the Persence object to it's initial state."""
        self._next_resident_id = 0
        self.residents = []



class Resident(utils.LogMixin, utils.CallbackMixin):
    def __init__(self, presence):
        super(Resident, self).__init__()
        self._init_callbacks(["presence_updated", "presence_changed"])
        self._presence = presence
        self.devices   = []

        self._id        = None
        self._name      = "Mr. X"
        self._email     = ""
        self._mobile    = ""
        self._pushover_token = ""

        self._presence_updated = None
        self._presence_changed = None
        self._present          = False


    @property
    def id(self):
        """The internal ID of the user. This must be a unique number within all residents."""
        return self._id


    @id.setter
    def id(self, val):
        self._id = val


    @property
    def name(self):
        """The name of the resident. This can be any kind of string you like to name your
        resident."""
        return self._name


    @name.setter
    def name(self, name):
        self._name = name


    @property
    def email(self):
        """The email address of the resident. You may use this to send mails to the resident
        from your scripts."""
        return self._email


    @email.setter
    def email(self, email):
        self._email = email


    @property
    def mobile(self):
        """The mobile number of the resident. You may use this to send SMS to the resident
        from your scripts."""
        return self._mobile


    @mobile.setter
    def mobile(self, mobile):
        self._mobile = mobile


    @property
    def pushover_token(self):
        """The pushover token of this resident. You may use this to send pushover messages
        to the resident from your scripts. Please take a look at the pmatic notification
        documentation (:mod:`pmatic.notify`) for details."""
        return self._pushover_token


    @pushover_token.setter
    def pushover_token(self, pushover_token):
        self._pushover_token = pushover_token


    @property
    def present(self):
        """Is ``True`` when the user is present and ``False`` when not."""
        return self._present


    @property
    def last_updated(self):
        """Is set to the unix timestamp of the last update or ``None`` when not updated yet."""
        return self._presence_updated


    @property
    def last_changed(self):
        """Is set to the unix timestamp of the last presence
        change or ``None`` when not updated yet."""
        return self._presence_changed


    def from_config(self, cfg):
        self._id      = cfg["id"]
        self._name    = cfg["name"]
        self._email   = cfg["email"]
        self._mobile  = cfg["mobile"]
        self._pushover_token = cfg["pushover_token"]

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
            "id"             : self._id,
            "name"           : self._name,
            "email"          : self._email,
            "mobile"         : self._mobile,
            "pushover_token" : self._pushover_token,
            "devices" : [ d.to_config() for d in self.devices ],
        }


    def from_state(self, state):
        self._presence_updated = state["presence_updated"]
        self._presence_changed = state["presence_changed"]
        self._present          = state["present"]

        for device, device_state in zip(self.devices, state["devices"]):
            device.from_state(device_state)


    def to_state(self):
        return {
            "presence_updated" : self._presence_updated,
            "presence_changed" : self._presence_changed,
            "present"          : self._present,
            "devices"          : [ d.to_state() for d in self.devices ],
        }


    def add_device(self, device):
        """Adds a :class:`PersonalDevice` object to the resident. Please note that
        you need to use a specific class inherited from :class:`PersonalDevice`,
        for example the :class:`PersonalDeviceFritzBoxHost` class."""
        self.devices.append(device)


    def clear_devices(self):
        """Resets the device list to it's initial state."""
        self.devices = []


    def update_presence(self):
        """Updates the presence of this resident. When at least one device is active,
        the resident is treated to be present."""
        if not self.devices:
            self.logger.debug("Has no devices associated. Not updating the presence.")
            return

        new_value = False
        for device in self.devices:
            device.update_presence()
            if device.active:
                new_value = True
                break

        self._set_presence(new_value)


    def _set_presence(self, new_value):
        """Internal helper for setting the presence state"""
        old_value = self._present

        now = time.time()
        self._presence_updated = now
        self._callback("presence_updated")

        self._present = new_value
        if new_value != old_value:
            self._presence_changed = now
            self._callback("presence_changed")


    def on_presence_updated(self, func):
        """Register a function to be called each time the presence of this resident is updated.

        The function must accept a single argument which is the the current :class:`Resident`
        object."""
        self.register_callback("presence_updated", func)


    def on_presence_changed(self, func):
        """Register a function to be called each time the presence of this resident is changed.

        The function must accept a single argument which is the the current :class:`Resident`
        object."""
        self.register_callback("presence_changed", func)



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
        """Restores the object attributes from the persisted configuration."""
        for key, val in cfg.items():
            setattr(self, "_" + key, val)


    def to_config(self):
        """Creates a dictionary which can be persisted and later loaded with :meth:`from_config`
        to reconstruct this object again."""
        return {
            "type_name": self.type_name,
        }


    def from_state(self, state):
        for key, val in state.items():
            setattr(self, "_" + key, val)


    def to_state(self):
        return {
            "active" : self._active,
            "name"   : self._name,
        }


    def update_presence(self):
        """Can be overridden by specific personal device classes to update the
        information of this device."""
        pass


    @property
    def name(self):
        """Provides the name of this device."""
        return self._name


    @property
    def active(self):
        """Whether or not this device is currently active."""
        return self._active



class PersonalDeviceFritzBoxHost(PersonalDevice, utils.LogMixin):
    type_name = "fritz_box_host"
    type_title = "fritz!Box Host"

    # Class wide connection handling (not per object)
    connection = None
    _address   = "fritz.box"
    _protocol  = "http"
    _port      = 49000
    _user      = ""
    _password  = ""

    @classmethod
    def configure(cls, address=None, protocol=None, port=None, user=None, password=None):
        if address != None:
            cls._address = address
        if protocol != None:
            cls._protocol = protocol
        if port != None:
            cls._port = port
        if user != None:
            cls._user = user
        if password != None:
            cls._password = password


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
        self._mac        = None


    @property
    def mac(self):
        """Provides the MAC address of this device."""
        return self._mac


    @mac.setter
    def mac(self, mac):
        if not re.match("^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$", mac):
            raise PMUserError("The given MAC address ins not valid.")
        self._mac = mac


    def to_config(self):
        """Creates a dictionary which can be persisted and later loaded with :meth:`from_config`
        to reconstruct this object again."""
        cfg = super(PersonalDeviceFritzBoxHost, self).to_config()
        cfg["mac"] = self.mac
        return cfg


    def to_state(self):
        """Returns the variable aspects of this object which can change during runtime."""
        state = super(PersonalDeviceFritzBoxHost, self).to_state()
        state["ipaddress"] = self._ip_address
        return state


    def update_presence(self):
        """Update the presence information of this device."""
        self._update_host_info()


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
        except requests.exceptions.RequestException as e:
            self.logger.info("Failed to update the host info: %s" % e)
            self.logger.debug("Traceback:", exc_info=True)
            return

        self._ip_address = result.ipaddress
        self._name       = result.hostname
        self._active     = result.active
