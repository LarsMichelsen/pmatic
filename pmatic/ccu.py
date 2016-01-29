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

import re

import pmatic.api
import pmatic.events
import pmatic.utils as utils
from pmatic.entities import Devices, Device, Rooms, Room
from pmatic.exceptions import PMException


class CCU(object):
    """Provides the simple to use access to the CCU.

    This is the main object to be used with pmatic. It provides top level
    access to all kind of entities like devices, channels, parameters, rooms
    and so on. It is possible to either poll information from the CCU or
    wait for incoming state update events provided by the CCU.

    If your program is executed right on the CCU, you don't need to provide
    any of the optional arguments.

    The optional arguments *address* and *credentials* are needed if you execute
    your program not on the CCU. You need to provide the host address of the
    CCU, which can be an IP address or resolvable host name as *address* argument.
    The *credentials* need to be given as two element tuple of username and password,
    for example ``("admin", "secretpw")`` which are then used to access the CCU.

    The default TCP connect timeout for the HTTP requests to the CCU is set to
    10 seconds. If you like to change the timeout, you need to set the argument
    *connect_timeout* to a number of seconds of your choice.

    """
    def __init__(self, **kwargs):
        """__init__([address[, credentials[, connect_timeout=10]]])
        """
        super(CCU, self).__init__()
        self.api = pmatic.api.init(**kwargs)
        self.rssi = None
        self._devices = None
        self._events = None
        self._rooms = None


    @property
    def devices(self):
        """This property provides access to the collection of all known devices.

        The collection is an :class:`pmatic.entities.Devices` instance."""
        if self._devices == None:
            self._devices = CCUDevices(self)
        return self._devices


    @property
    def events(self):
        """Using this property you can use the XML-RPC event listener of pmatic.

        Provides access to the XML-RPC :class:`pmatic.events.EventListener` instance."""
        if not self._events:
            self._events = pmatic.events.EventListener(self)
        return self._events


    @property
    def rooms(self):
        """Provides access to the collection of all known rooms.

        This collection is an :class:`pmatic.entities.Rooms` instance."""
        if self._rooms == None:
            self._rooms = CCURooms(self)
        return self._rooms


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
            self.RSSI = pmatic.api.SignalStrength(self.api)
        return self.RSSI



class CCUDevices(Devices):
    """The central device management class.

    CCUDevices class is just like the :class:`Devices` class, with the difference that it provides the
    :meth:`query` method which can be used to create new :class:`Devices` collections. Another difference
    is that it is initializing all devices when generic methods to access the devices are called."""
    def __init__(self, ccu):
        super(CCUDevices, self).__init__(ccu)
        self._device_specs = pmatic.api.DeviceSpecs(ccu.api)
        self._device_logic = pmatic.api.DeviceLogic(ccu.api)
        self._initialized = False


    @property
    def _devices(self):
        """Optional initializer of the devices data structure, called on first access."""
        if not self._initialized:
            self._init_all_devices()
            self._initialized = True
        return self._device_dict


    def _add_without_init(self, device):
        self._device_dict[device.address] = device


    # FIXME: Documentation about possible filters: device_type=None, device_name=None, device_name_regex=None, has_channel_ids=None):
    # FIXME: Add more filter options
    def query(self, **filters):
        devices = Devices(self._ccu)
        for device in self._query_for_devices(**filters):
            self._add_without_init(device)
            devices.add(device)

        return devices


    def _query_for_devices(self, **filters):
        if "device_type" in filters and utils.is_string(filters["device_type"]):
            filters["device_type"] = [filters["device_type"]]

        for address, spec in self._device_specs.items():
            # First try to get an olready created room object from the central
            # CCU room collection. Otherwise create the room object and add it
            # to the central collection and this collection.
            device = self._device_dict.get(address)
            if not device:
                device = self._create_from_low_level_dict(spec)

            # Now perform optional filtering

            # Filter by device type
            if "device_type" in filters and device.type not in filters["device_type"]:
                continue

            # Exact match device name
            if "device_name" in filters and filters["device_name"] != device.name:
                continue

            # regex match device name
            if "device_name_regex" in filters and not re.match(filters["device_name_regex"], device.name):
                continue

            # Add devices which have one of the channel ids listed in has_channel_ids
            if "has_channel_ids" in filters \
               and not [ c for c in device.channels if c.id in filters["has_channel_ids"] ]:
                continue

            yield device


    def _init_all_devices(self):
        """Adds all devices known to the CCU to this collection.

        It is called to initialize the devices on the first accessor method call. It initializes the
        device collections once. You can enforce the collection too be re-initialized by calling
        :meth:`clear` and then call an accessor again."""
        for device in self._query_for_devices():
            self._add_without_init(device)


    def add_from_low_level_dict(self, spec):
        """Creates a device object and add it to the collection.

        This method can be used to create a device object by providing a valid
        low level attributes dictionary specifying an object.

        It creates the device and also assigns the logic level attributes to
        the object so that it is a fully initialized device object.
        """
        self.add(self._create_from_low_level_dict(spec))


    def _create_from_low_level_dict(self, spec):
        """Creates a device object from a low level device spec."""
        device = Device.from_dict(self._ccu, spec)
        device.set_logic_attributes(self._device_logic[device.address])
        return device


    def clear(self):
        """Remove all objects from this devices collection."""
        self._devices.clear()
        self._initialized = False



class CCURooms(Rooms):
    """Manages a collection of rooms."""

    def __init__(self, ccu):
        super(CCURooms, self).__init__(ccu)
        if not isinstance(ccu, CCU):
            raise PMException("Invalid ccu object provided: %r" % ccu)
        self._ccu = ccu
        self._initialized = False



    @property
    def _rooms(self):
        """Optional initializer of the rooms data structure, called on first access."""
        if not self._initialized:
            self._room_dict = {}
            self._init_all_rooms()
            self._initialized = True
        return self._room_dict


    def _add_without_init(self, room):
        self._room_dict[room.id] = room


    # FIXME: Add filter options
    def query(self, **filters):
        rooms = Rooms(self._ccu)
        for room in self._query_for_rooms(**filters):
            self._add_without_init(room)
            rooms.add(room)

        return rooms


    def _query_for_rooms(self, **filters):
        """Initializes the list of rooms for this collection.

        When the rooms have not been fetched yet, the room specs might be fetched
        from the CCU.

        You can enforce reinitialization by first calling :meth:`clear` and the access the data
        of this instance again.
        """

        for room_dict in self._ccu.api.room_get_all():
            # First try to get an olready created room object from the central
            # CCU room collection. Otherwise create the room object and add it
            # to the central collection and this collection.
            room = self._room_dict.get(int(room_dict["id"]))
            if not room:
                room = Room(self._ccu, room_dict)

            # Now perform optional filtering

            yield room


    def _init_all_rooms(self):
        """Adds all rooms known to the CCU to this collection.

        It is called to initialize the rooms on the first accessor method call. It initializes the
        collections once. You can enforce the collection too be re-initialized by calling
        :meth:`clear` and then call an accessor again."""
        for room in self._query_for_rooms():
            self._add_without_init(room)


    def clear(self):
        """Remove all :class:`Room` objects from this collection."""
        self._rooms.clear()
        self._initialized = False
