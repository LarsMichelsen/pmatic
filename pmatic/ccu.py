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

try:
    # Is recommended for Python 3.x but fails on 2.7, but is not mandatory
    from builtins import object
except ImportError:
    pass

try:
    # Python 2.x
    import __builtin__ as builtins
except ImportError:
    # Python 3+
    import builtins

import re
import threading

import pmatic.api
import pmatic.events
import pmatic.utils as utils
from pmatic.entities import Devices, Device, Rooms, Room
from pmatic.residents import Residents


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
        if hasattr(self, "api"):
            return # Skip second __init__ of pmatic manager CCU instances (see __new__ below)

        super(CCU, self).__init__()
        self.api = pmatic.api.init(**kwargs)
        self._rssi = None
        self._devices = None
        self._events = None
        self._rooms = None
        self._residents = None


    def __new__(cls, **kwargs):
        """This special method is used to prevent creation of a new CCU object by scripts which are
        executed with the option "run inline" by the pmatic manager.

        In this mode the scripts are not executed as separate process, but in the context of the
        pmatic manager. This mode has been implemented to provide direct access to the already
        fully initialized CCU() object off the pmatic manager. So scripts can access all devices,
        channels, values etc. without the need to fetch them on their own from the CCU. This makes
        running scripts running a lot faster while producing a very small load.

        This method makes it possible to use regular pmatic scripts which create their own
        CCU object and connect to the CCU on their own when run as dedicated programs within the
        contxt of the pmatic manager and use the CCU object of the manager when executed in
        "run inline" mode.

        But this only works as intended after the connection of the manager with the CCU has been
        initialized. So better not use the "on startup of manager" condition for this.

        We need to override the __new__ instead of e.g. use a factory to keep the API of the
        pmatic scripts equal in all pmatic script use cases.
        """
        if hasattr(builtins, "manager_ccu"):
            return builtins.manager_ccu
        else:
            return super(CCU, cls).__new__(cls)


    @property
    def devices(self):
        """This property provides access to the collection of all known devices.

        This collection is an instance of :class:`pmatic.ccu.CCUDevices`, which is a subclass
        of the room collection class :class:`pmatic.entities.Devices`."""
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

        This collection is an instance of :class:`pmatic.ccu.CCURooms`, which is a subclass
        of the room collection class :class:`pmatic.entities.Rooms`."""
        if self._rooms == None:
            self._rooms = CCURooms(self)
        return self._rooms


    @property
    def residents(self):
        """Provides access to the resident and presence management functionality of pmatic.
        See :class:`pmatic.residents.Residents` for details."""
        if self._residents == None:
            self._residents = Residents()
        return self._residents


    @property
    def interfaces(self):
        """Provides a list of available CCU communication interfaces.

        Example output:
            [ {u'info': u'BidCos-RF', u'name': u'BidCos-RF', u'port': 2001},
              {u'info': u'Virtual Devices', u'name': u'VirtualDevices', u'port': 9292} ]
        """
        return self.api.interface_list_interfaces()


    @property
    def bidcos_interfaces(self):
        """Provides a list of all BidCos interfaces of the CCU.

        Example output:
          [{u'address': u'KEQ0714972',
            u'description': u'',
            u'duty_cycle': 0,
            u'is_connected': True,
            u'is_default': True}]
        """
        interfaces = []
        for interface in self.api.interface_list_bidcos_interfaces(
                                                    interface="BidCos-RF"):
            new = {}
            for key, val in interface.items():
                if key == "dutyCycle":
                    val = int(val)
                new[utils.decamel(key)] = val
            interfaces.append(new)

        return interfaces


    # FIXME: Consolidate API with self.devices.(...)
    @property
    def signal_strengths(self):
        if self._rssi == None:
            self._rssi = pmatic.api.SignalStrength(self.api)
        return self._rssi


    def close(self):
        """Is used to close the connections with the CCU and the eventual open event listener"""
        self.api.close()
        if self._events:
            self.events.close()



class CCUDevices(Devices):
    """The central device management class.

    CCUDevices class is just like the :class:`.pmatic.entities.Devices` class, with the difference
    that it provides the :meth:`.CCUDevices.query` method which can be used to create new
    :class:`.pmatic.entities.Devices` collections. Another difference is, that it is initializing
    all devices configured in the CCU as device objects when generic methods to access the devices
    like :func:`len` are called on the object."""

    def __init__(self, ccu):
        super(CCUDevices, self).__init__(ccu)
        self._device_specs = pmatic.api.DeviceSpecs(ccu.api)
        self._device_logic = pmatic.api.DeviceLogic(ccu.api)

        self._initialized = False
        self._init_lock   = threading.RLock()


    @property
    def _devices(self):
        """Optional initializer of the devices data structure, called on first access."""
        with self._init_lock:
            if not self._initialized:
                self._init_all_devices()
                self._initialized = True
            return self._device_dict


    @property
    def initialized(self):
        """Full initialization of the device collection.

        :getter: Whether or not the devices collection has been fully initialized.
        :setter: Sets the device collection to initialized state (Only for internal use)
        :type: bool
        """
        return self._initialized


    @initialized.setter
    def initialized(self, value):
        self._initialized = value


    def _add_without_init(self, device):
        self._device_dict[device.address] = device


    def query(self, **filters):
        """query([device_type=None[, device_name=None[, device_name_regex=None[, device_address=None ]]]])
        Use this function to query the CCU for a collection of devices.

        The devices are returned in a :class:`.pmatic.entities.Devices` collection.
        Additionally the device objects are cached in the centrall :class:`.pmatic.CCU` object for
        later reference, when e.g. another search is asking for the same device. In
        case the same object is returned.

        The object can be filtered using different filter parameters.

        The *device_type*
        can be used to either search for devices of one specific or multiple types. The
        device type needs to be given as string which needs to be the exact product name,
        for example ``device_type="HM-Sec-SC"``. If you want to get multiple device types,
        you can do it like this: ``device_type=["HM-Sec-SC", "HM-CC-RT-DN"]``.

        You can also search for specific devices by their names. The first option is to
        search for the exact name of one single device by setting the *device_name* to the
        name of the device, for example: ``device_name="Wohnzimmer-Fenster"``. Please note
        that this filter is case sensitive and a full exact match for the device name.

        If you need more flexible filtering by the name, you can use the *device_name_regex*
        filter. You can either provide a regex in form of a string which is then matched
        with the device name from the start of the name (prefix match).
        One example to match all device names ending with *-Fenster*:
        ``device_name_regex=".*-Fenster$"``.
        You can also provide the result of :func:`re.compile` as value of *device_name_regex*.
        This is useful if you want to specify some special regex flags for your matching regex.

        The *device_address* can be used to get a specific device by it's address. This is an
        exact match filter. So you can either get a device collection of one device or an empty
        one back.
        """
        devices = Devices(self._ccu)
        for device in self._query_for_devices(**filters):
            self._add_without_init(device)
            devices.add(device)

        return devices


    def _query_for_devices(self, **filters):
        if "device_type" in filters and utils.is_string(filters["device_type"]):
            filters["device_type"] = [filters["device_type"]]

        for address, spec in self._device_specs.items():
            # First try to get an already created room object from the central
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
            if "device_name_regex" in filters \
               and not re.match(filters["device_name_regex"], device.name):
                continue

            # Add devices which have one of the channel ids listed in has_channel_ids
            if "has_channel_ids" in filters \
               and not [ c for c in device.channels if c.id in filters["has_channel_ids"] ]:
                continue

            # exact device address match
            if "device_address" in filters and device.address != filters["device_address"]:
                continue

            yield device


    def _init_all_devices(self):
        """Adds all devices known to the CCU to this collection.

        It is called to initialize the devices on the first accessor method call. It initializes
        the device collections once. You can enforce the collection too be re-initialized by
        calling :meth:`clear` and then call an accessor again."""
        for device in self._query_for_devices():
            self._add_without_init(device)


    def add_from_low_level_dict(self, spec):
        """Creates a device object and add it to the collection.

        This method can be used to create a device object by providing a valid
        low level attributes dictionary specifying an object.

        It creates the device and also assigns the logic level attributes to
        the object so that it is a fully initialized device object.
        """
        self._add_without_init(self._create_from_low_level_dict(spec))


    def _create_from_low_level_dict(self, spec):
        """Creates a device object from a low level device spec."""
        device = Device.from_dict(self._ccu, spec)
        device.set_logic_attributes(self._device_logic[device.address])
        return device


    def clear(self):
        """Remove all objects from this devices collection."""
        if self._initialized:
            self._devices.clear()
            self._initialized = False


    @property
    def already_initialized_devices(self):
        """Provides access to the already known devices without fetching new ones.

        Directly provices access to the device dictionary where the address of the devices
        is used as key and the device objects are the values.

        Only for internal use."""
        return self._device_dict



class CCURooms(Rooms):
    """The central room management class.

    The :class:`.CCURooms` class is just like the :class:`.pmatic.entities.Rooms` class, with the
    difference that it provides the :meth:`.CCURooms.query` method which can be used to create new
    :class:`.pmatic.entities.Rooms` collections. Another difference is, that it is initializing
    all rooms configured in the CCU as room objects when generic methods to access the rooms
    like :func:`len` are called on the object."""

    def __init__(self, ccu):
        super(CCURooms, self).__init__(ccu)
        self._initialized = False
        self._init_lock = threading.RLock()


    @property
    def _rooms(self):
        """Optional initializer of the rooms data structure, called on first access."""
        with self._init_lock:
            if not self._initialized:
                self._room_dict = {}
                self._init_all_rooms()
                self._initialized = True
            return self._room_dict


    def _add_without_init(self, room):
        self._room_dict[room.id] = room


    def query(self, **filters):
        """query([room_name=None[, room_name_regex=None]])
        Use this function to query the CCU for a collection of rooms.

        The room objects are returned in a :class:`.pmatic.entities.Rooms` collection.
        Additionally the room objects are cached in the central :class:`.pmatic.CCU` object for
        later reference, when e.g. another search is asking for the same room. In
        case the same object is returned.

        The object can be filtered using different filter parameters.

        You can search for specific rooms by their names. The first option is to
        search for the exact name of one single room by setting the *room_name* to the
        name of the room, for example: ``room_name="Wohnzimmer"``. Please note
        that this filter is case sensitive and a full exact match for the room name.

        If you need more flexible filtering by the name, you can use the *room_name_regex*
        filter. You can either provide a regex in form of a string which is then matched
        with the room name from the start of the name (prefix match).
        One example to match all room names ending with *-2-Floor*:
        ``room_name_regex=".*-2-Floor$"``.
        You can also provide the result of :func:`re.compile` as value of *room_name_regex*.
        This is useful if you want to specify some special regex flags for your matching regex.
        """
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

            # Exact match device name
            if "room_name" in filters and filters["room_name"] != room.name:
                continue

            # regex match device name
            if "room_name_regex" in filters \
               and not re.match(filters["room_name_regex"], room.name):
                continue

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
