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

try:
    # Is recommended for Python 3.x but fails on 2.7, but is not mandatory
    from builtins import object
except ImportError:
    pass

import time

import pmatic.api
import pmatic.events
import pmatic.utils as utils
from pmatic.exceptions import PMException
from pmatic.entities import Device


class CCU(object):
    """Defines the central object of more complex pmatic use cases.

    If you not only want to deal with states fetched from the CCU but also
    use them together with events received via the XML-RPC API of the CCU,
    the CCU object should be used as central manager.
    """
    def __init__(self, **kwargs):
        super(CCU, self).__init__()
        self.api = pmatic.api.init(**kwargs)
        self.rssi = None
        self._devices = None
        self._events = None


    @property
    def devices(self):
        """Provides access to the collection of all known devices."""
        if not self._devices:
            self._devices = Devices(self.api)
        return self._devices


    @property
    def events(self):
        """Provides access to the pmatic XML-RPC EventListener instance."""
        if not self._events:
            self._events = pmatic.events.EventListener(self)
        return self._events


    def interfaces(self):
        """Returns a list of available CCU communication interfaces.

        Example output:
            [ {u'info': u'BidCos-RF', u'name': u'BidCos-RF', u'port': 2001},
              {u'info': u'Virtual Devices', u'name': u'VirtualDevices', u'port': 9292} ]
        """
        return self.api.interface_list_interfaces()


    def bidcos_interfaces(self):
        """Returns a list of all BidCos interfaces of the CCU.

        Example output:
          [{u'address': u'KEQ0714972',
            u'description': u'',
            u'dutyCycle': u'0',
            u'isConnected': True,
            u'isDefault': True}]
        """
        return self.api.interface_list_bidcos_interfaces(interface="BidCos-RF")


    # FIXME: Consolidate API with self.devices.(...)
    def signal_strengths(self):
        if self.RSSI == None:
            self.RSSI = SignalStrength(self.api)
        return self.RSSI



class Devices(object):
    """Manages a collection of CCU devices."""

    def __init__(self, api):
        super(Devices, self).__init__()
        self._api = api
        self._devices = {}
        self._device_specs = DeviceSpecs(api)


    # FIXME: Add filter options
    def get(self):
        """Returns all device objects matching the provided filters.

        When the devices have not been fetched yet, the device specs might be fetched
        from the CCU and objects are created for all devices."""
        requested = []
        for address, spec in self._device_specs.items():
            #import pprint ; pprint.pprint(spec)
            device = self._devices.setdefault(address, Device.from_dict(self._api, spec))
            requested.append(device)
        return requested


    def add_from_dict(self, spec):
        """Creates a device object and add it to the collection.

        This method can be used to create a device object by providing a valid
        dictionary specifying an object.
        """
        self.add(Device.from_dict(self._api, spec))


    def add(self, device):
        """Add a device object tot the collection."""
        if not isinstance(device, Device):
            raise PMException("You can only add device objects.")
        self._devices[device.address] = device


    # FIXME: Trigger device spec fetch?
    def exists(self, address):
        """Check whether or not a device with the given address is in this collection."""
        return address in self._devices


    # FIXME: Trigger device spec fetch?
    def addresses(self):
        """Returns a list of all addresses of all initialized devices."""
        return self._devices.keys()


    def delete(self, address):
        """Deletes the device with the given address from the pmatic runtime.

        The device is not deleted from the CCU.
        When the device is not known, the method is tollerating that."""
        try:
            del self._devices[address]
        except ValueError:
            pass


    # FIXME: Trigger device spec fetch?
    def get_device_or_channel_by_address(self, address):
        """Returns the device or channel object of the given address."""
        if ":" in address:
            device_address = address.split(":", 1)[0]
            return self._devices[device_address].channel_by_address(address)
        else:
            return self._devices[address]


    # FIXME: Trigger device spec fetch?
    def __iter__(self):
        for value in self._devices.values():
            yield value



class DeviceSpecs(pmatic.api.CachedAPICall):
    """Uses the JSON-API to fetch the specifications of all devices and their channels.

    The CCU provides the same data as when the XML-RPC API is initialized and it
    responds with the first NEW_DEVICES call. But when init() has been executed
    before, then we already have these information and the XML-RPC API is not sending
    us the information again.
    """
    def _update(self):
        # Incoming dict keys are camel cased. uah.
        # The dict keys are directly handed over to the device/channel objects. So they
        # need ot be equalized and with internal naming specs just like the also different
        # keys from the XML-RPC messages.
        def decamel_dict_keys(d):
            for k in d:
                d[utils.decamel(k)] = d.pop(k)
            return d

        devices = {}
        for spec in self._api.interface_list_devices(interface="BidCos-RF"):
            spec = decamel_dict_keys(spec)
            if "parent" not in spec:
                devices[spec["address"]] = spec
            else:
                device = devices[spec["parent"]]
                channels = device.setdefault("channels", [])
                channels.append(spec)

        for key, val in devices.items():
            dict.__setitem__(self, key, val)



class SignalStrength(pmatic.api.CachedAPICall):
    """Fetches the signal strength information about all connected devices

    It caches these information for up to 360 seconds by default. The caching
    time can be set via constructor. Data can be accessed as in normal dicts.
    """
    def _update(self):
        for entry in self._api.interface_rssi_info(interface="BidCos-RF"):
            partner_dict = dict([(p["name"], p["rssiData"]) for p in entry["partner"] ])
            dict.__setitem__(self, entry["name"], partner_dict)
