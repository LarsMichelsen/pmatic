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

# Relevant docs:
# - http://www.eq-3.de/Downloads/PDFs/Dokumentation_und_Tutorials/HM_XmlRpc_V1_502__2_.pdf
# - http://www.eq-3.de/Downloads/PDFs/Dokumentation_und_Tutorials/HM_Script_Teil_4_Datenpunkte_1_503.pdf

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import time

try:
    # Is recommended for Python 3.x but fails on 2.7, but is not mandatory
    from builtins import object
except ImportError:
    pass

import pmatic.api
import pmatic.params
import pmatic.utils as utils
from pmatic.exceptions import PMException, PMDeviceOffline

class Entity(object):
    _transform_attributes = {}
    skip_attributes = []
    _mandatory_attributes = []

    def __init__(self, api, spec):
        assert isinstance(api, pmatic.api.AbstractAPI), "api is not of API class: %r" % api
        assert type(spec) == dict, "spec is not a dictionary: %r" % spec
        self._api = api
        self._set_attributes(spec)
        self._verify_mandatory_attributes()
        super(Entity, self).__init__()


    def _set_attributes(self, obj_dict):
        """Adding provided attributes to this entity.

        Transforming and filtering dictionaries containing attributes for this entity
        by using the configured transform methods for the individual attributes and also
        excluding some attributes which keys are in self.skip_attributes."""
        for key, val in obj_dict.items():
            if key in self.skip_attributes:
                continue

            # Optionally convert values using the given transform functions
            # for the specific object type
            trans_func = self._transform_attributes.get(key)
            if trans_func:
                func_type = type(trans_func).__name__
                if func_type in [ "instancemethod", "function", "method" ]:
                    args = []
                    offset = 1 if func_type in [ "instancemethod", "method" ] else 0
                    for arg_name in trans_func.__code__.co_varnames[offset:trans_func.__code__.co_argcount]:
                        if arg_name == "api":
                            args.append(self._api)
                        elif arg_name == "device":
                            args.append(self)
                        elif arg_name == "obj":
                            args.append(self)
                        else:
                            args.append(val)
                else:
                    args = [val]

                val = trans_func(*args)

            # Transform keys from camel case to our style
            key = utils.decamel(key)

            setattr(self, key, val)


    def _verify_mandatory_attributes(self):
        for key in self._mandatory_attributes:
            if not hasattr(self, key):
                raise PMException("The mandatory attribute \"%s\" is missing." % key)



class Channel(utils.LogMixin, Entity):
    _transform_attributes = {
        # ReGa attributes:
        "id"               : int,
        "partner_id"       : lambda x: None if x == "" else int(x),
        # Low level attributes:
        "aes_active"        : bool,
        "link_source_roles" : lambda v: v if type(v) == list else v.split(" "),
        "link_target_roles" : lambda v: v if type(v) == list else v.split(" "),
    }

    # Don't add these keys to the objects attributes
    skip_attributes = [
        # Low level attributes:
        "parent",
        "parent_type",
    ]

    # These keys have to be set after attribute initialization
    _mandatory_attributes = [
        # Low level attributes:

        # address of channel
        "address",
        # communication direction of channel:
        # 0 = DIRECTION_NONE (Kanal unterstützt keine direkte Verknüpfung)
        # 1 = DIRECTION_SENDER
        # 2 = DIRECTION_RECEIVER
        "direction",
        # see device flags (0x01 visible, 0x02 internal, 0x08 can not be deleted)
        "flags",
        # channel number
        "index",
        # possible roles as sender
        "link_source_roles",
        # possible roles as receiver
        "link_target_roles",
        # list of available parameter sets
        "paramsets",
        # type of this channel
        "type",
        # version of the channel description
        "version",
    ]

    def __init__(self, device, spec):
        assert isinstance(device, Device), "device object is not a Device derived class: %r" % device
        self.device = device
        self._values = {}
        super(Channel, self).__init__(device._api, spec)


    @classmethod
    def from_channel_dicts(cls, device, channel_dicts):
        channel_objects = []
        for channel_dict in channel_dicts:
            channel_class = channel_classes_by_type_name.get(channel_dict["type"], Channel)

            if channel_class == Channel:
                cls.cls_logger().debug("Using generic Channel class (Type: %s): %r" % (channel_dict["type"], channel_dict))

            channel_objects.append(channel_class(device, channel_dict))
        return channel_objects


    def _init_value_specs(self):
        """Initializes the value objects by fetching the specification from the CCU.

        The specification (description) of the VALUES paramset are fetched from
        the CCU and Parameter() objects will be created from them. Then they
        will be added to self._values.

        This method is called on the first access to the values.
        """
        self._values.clear()
        for param_spec in self._api.interface_get_paramset_description(interface="BidCos-RF",
                                                    address=self.address, paramsetType="VALUES"):
            param_id = param_spec["ID"]

            class_name = "Parameter%s" % param_spec["TYPE"]
            cls = getattr(pmatic.params, class_name)
            if not cls:
                self.logger.warning("%s: Skipping unknown parameter %s of type %s. Class %s not implemented." %
                                              (self.channel_type, param_id, param_spec["TYPE"], class_name))
            else:
                self._values[param_id] = cls(self, param_spec)


    def _value_update_needed(self):
        """Tells whether or not the set of  values should be fetched from the CCU."""
        oldest_value_time = None
        for param in self._values.values():
            try:
                last_updated = param.last_updated
                if last_updated == None:
                    last_updated = 0 # enforce the update
            except PMException:
                continue # Ignore not readable values

            if oldest_value_time == None:
                oldest_value_time = last_updated
            elif last_updated < oldest_value_time:
                oldest_value_time = last_updated

        if oldest_value_time == None:
            return False # No readable value at all

        # FIXME: Make threshold configurable
        return oldest_value_time <= time.time() - 60


    def _fetch_values(self):
        """Fetches all values of the channel.

        Gathers the values of the channel and updates the value parameters in self._values.
        The parameter objects need to be initialized before (self._init_value_specs).
        """
        if not self._values:
            raise PMException("The value parameters are not yet initialized.")

        try:
            values = self._api.interface_get_paramset(interface="BidCos-RF",
                                         address=self.address,paramsetKey="VALUES")
        except PMException as e:
            # FIXME: Clean this 601 in "%s" up!
            if "601" in ("%s" % e) and not self.device.is_online:
                raise PMDeviceOffline("Failed to fetch the values. The device is not online.")
            else:
                raise

        for param_id, value in values.items():
            self._values[param_id]._set_from_api(value)


    def set_logic_attributes(self, attrs):
        """Used to update the logic attributes of this channel.

        Applying the attributes in the dictionary to this object. Special handling
        for some attributes which are already set by the low level attributes."""
        #import pprint
        #pprint.pprint(self.__dict__)
        #pprint.pprint(attrs)
        #sys.exit(1)
        # Skip non needed attributes (already set by low level data)
        # FIXME: 'direction': 1, from low level API might be duplicate of u'category': u'CATEGORY_SENDER',
        # FIXME: 'aes_active': True, from low level API might be duplicate of u'mode': u'MODE_AES',
        attrs = attrs.copy()
        for a in [ "address", "device_id" ]:
            del attrs[a]

        self._set_attributes(attrs)


    @property
    def values(self):
        """Provides access to all value objects of this channel."""
        if not self._values:
            self._init_value_specs()

        if self._value_update_needed():
            self._fetch_values()

        return self._values


    def summary_state(self):
        """Represents a summary state of the channel.

        Formats values and titles of channel values and returns them as string.

        Default formating of channel values. Concatenates titles and values of
        all channel values except the maintenance channel.
        The values are sorted by the titles."""
        formated = []
        for title, value in sorted([ (v.title, v) for v in self.values.values() if v.readable ]):
            formated.append("%s: %s" % (title, value))
        return ", ".join(formated)


    def on_value_changed(self, func):
        """Register a function to be called each time a value of this channel parameters has changed."""
        for value in self.values.values():
            value.register_callback("value_changed", func)


    def on_value_updated(self, func):
        """Register a function to be called each time a value of this channel parameters has been updated."""
        for value in self.values.values():
            value.register_callback("value_updated", func)



# FIXME: Implement this
class ChannelMaintenance(Channel):
    type_name = "MAINTENANCE"
    name = "Maintenance"
    id = 0 # FIXME: Really no id for maintenance channels?

    def summary_state(self):
        """The maintenance channel does not provide a summary state.

        If you want to get a formated maintenance state, you need to call maintenance_state()."""
        pass

    def maintenance_state(self):
        super(self, ChannelMaintenance).summary_state()



# FIXME: Handle LOWBAT/ERROR
class ChannelShutterContact(Channel):
    type_name = "SHUTTER_CONTACT"

    def is_open(self):
        return self.values["STATE"].value


    def summary_state(self):
        return self.is_open() and "open" or "closed"



# FIXME: Handle INHIBIT, WORKING
class ChannelSwitch(Channel):
    type_name = "SWITCH"

    def is_on(self):
        return self.values["STATE"].value


    def summary_state(self):
        return "%s: %s" % (self.values["STATE"].title, self.is_on() and "on" or "off")


    def toggle(self):
        if self.is_on():
            return self.switch_off()
        else:
            return self.switch_on()


    def switch_off(self):
        return self.values["STATE"].set(False)


    def switch_on(self):
        return self.values["STATE"].set(True)



# FIXME: Handle LED_STATUS, ALL_LEDS, LED_SLEEP_MODE, INSTALL_TEST
class ChannelKey(Channel):
    type_name = "KEY"


    def press_short(self):
        return self.values["PRESS_SHORT"].set(True)


    def press_long(self):
        return self.values["PRESS_LONG"].set(True)


    # Not verified working
    def press_long_release(self):
        return self.values["PRESS_LONG_RELEASE"].set(True)


    # Not verified
    def press_cont(self):
        return self.values["PRESS_CONT"].set(True)


    def summary_state(self):
        return None # has no state info as it's a toggle button



class ChannelVirtualKey(ChannelKey):
    type_name = "VIRTUAL_KEY"



# FIXME: Handle all values:
# {u'POWER': u'3.520000', u'ENERGY_COUNTER': u'501.400000', u'BOOT': u'1',
#  u'CURRENT': u'26.000000', u'FREQUENCY': u'50.010000', u'VOLTAGE': u'228.900000'}
class ChannelPowermeter(Channel):
    type_name = "POWERMETER"


# FIXME: To be implemented.
class ChannelConditionPower(Channel):
    type_name = "CONDITION_POWER"


# FIXME: To be implemented.
class ChannelConditionCurrent(Channel):
    type_name = "CONDITION_CURRENT"


# FIXME: To be implemented.
class ChannelConditionVoltage(Channel):
    type_name = "CONDITION_VOLTAGE"



# FIXME: To be implemented.
class ChannelConditionFrequency(Channel):
    type_name = "CONDITION_FREQUENCY"



# FIXME: To be implemented.
class ChannelWeather(Channel):
    type_name = "WEATHER"



# FIXME: Handle ERROR
class ChannelClimaVentDrive(Channel):
    type_name = "CLIMATECONTROL_VENT_DRIVE"



# FIXME: Handle ADJUSTING_COMMAND, ADJUSTING_DATA
class ChannelClimaRegulator(Channel):
    type_name = "CLIMATECONTROL_REGULATOR"

    def summary_state(self):
        val = self.values["SETPOINT"]
        if val == 0.0:
            return "Ventil closed"
        elif val == 100.0:
            return "Ventil open"
        else:
            return "Ventil: %s" % self.values["SETPOINT"]


# Devices:
#  HM-CC-RT-DN
# FIXME: Values:
# {u'SET_TEMPERATURE': u'21.500000', u'PARTY_START_MONTH': u'1', u'BATTERY_STATE': u'2.400000', u'PARTY_START_DAY': u'1', u'PARTY_STOP_DAY': u'1', u'PARTY_START_YEAR': u'0', u'FAULT_REPORTING': u'0', u'PARTY_STOP_TIME': u'0', u'ACTUAL_TEMPERATURE': u'23.100000', u'BOOST_STATE': u'15', u'PARTY_STOP_YEAR': u'0', u'PARTY_STOP_MONTH': u'1', u'VALVE_STATE': u'10', u'PARTY_START_TIME': u'450', u'PARTY_TEMPERATURE': u'5.000000', u'CONTROL_MODE': u'1'}
class ChannelClimaRTTransceiver(Channel):
    type_name = "CLIMATECONTROL_RT_TRANSCEIVER"

    def summary_state(self):
        return "Temperature: %s (Target: %s)" % \
                (self.values["ACTUAL_TEMPERATURE"], self.values["SET_TEMPERATURE"])



# Has not any values
class ChannelWindowSwitchReceiver(Channel):
    type_name = "WINDOW_SWITCH_RECEIVER"

    def summary_state(self):
        return None


# Has not any values
class ChannelWeatherReceiver(Channel):
    type_name = "WEATHER_RECEIVER"

    def summary_state(self):
        return None


# Devices:
#  HM-CC-RT-DN
# Has not any values
class ChannelClimateControlReceiver(Channel):
    type_name = "CLIMATECONTROL_RECEIVER"

    def summary_state(self):
        return None


# Devices:
#  HM-CC-RT-DN
# Has not any values
class ChannelClimateControlRTReceiver(Channel):
    type_name = "CLIMATECONTROL_RT_RECEIVER"

    def summary_state(self):
        return None


# Devices:
#  HM-CC-RT-DN
# Has not any values
class ChannelRemoteControlReceiver(Channel):
    type_name = "REMOTECONTROL_RECEIVER"

    def summary_state(self):
        return None



class Devices(object):
    """Manages a collection of CCU devices."""

    def __init__(self, api):
        super(Devices, self).__init__()
        if not isinstance(api, pmatic.api.AbstractAPI):
            raise PMException("Invalid api object provided: %r" % api)
        self._api = api
        self._devices = {}
        self._device_specs = pmatic.api.DeviceSpecs(api)
        self._device_logic = pmatic.api.DeviceLogic(api)


    # FIXME: Add more filter options
    def get(self, device_type=None, device_name=None, device_name_regex=None, has_channel_ids=None):
        """Returns all device objects matching the provided filters.

        When the devices have not been fetched yet, the device specs might be fetched
        from the CCU and objects are created for all devices."""

        if utils.is_string(device_type):
            device_type = [device_type]

        # Create new device group which is returned as result for this query
        group = Devices(self._api)

        for address, spec in self._device_specs.items():
            # First create the device objects
            device = self._devices.get(address)
            if not device:
                device = self._create_from_low_level_dict(spec)

            # Now perform optional filtering

            # Filter by device type
            if device_type != None and device.type not in device_type:
                continue

            # Exact match device name
            if device_name != None and device_name != device.name:
                continue

            # regex match device name
            if device_name_regex != None and not re.match(device_name_regex, device.name):
                continue

            # Add devices which have one of the channel ids listed in has_channel_ids
            if has_channel_ids != None and not [ c for c in device.channels if c.id in has_channel_ids ]:
                continue

            self._devices[address] = device
            group.add(device)
        return group


    def _create_from_low_level_dict(self, spec):
        """Creates a device object from a low level device spec."""
        device = Device.from_dict(self._api, spec)
        device.set_logic_attributes(self._device_logic[device.address])
        return device


    def add_from_low_level_dict(self, spec):
        """Creates a device object and add it to the collection.

        This method can be used to create a device object by providing a valid
        low level attributes dictionary specifying an object.

        It creates the device and also assigns the logic level attributes to
        the object so that it is a fully initialized device object.
        """
        self.add(self._create_from_low_level_dict(spec))


    def add(self, device):
        """Add a :class:`.Device` object to the collection."""
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
        except KeyError:
            pass


    def clear(self):
        """Remove all objects from this devices collection."""
        self._devices.clear()


    # FIXME: Trigger device spec fetch?
    def get_device_or_channel_by_address(self, address):
        """Returns the device or channel object of the given address.

        Raises a KeyError exception when no device exists for this
        address in the already fetched objects."""
        if ":" in address:
            device_address = address.split(":", 1)[0]
            return self._devices[device_address].channel_by_address(address)
        else:
            return self._devices[address]


    # FIXME: Trigger device spec fetch?
    def __iter__(self):
        for value in self._devices.values():
            yield value


    def __len__(self):
        return len(self._devices)


    def on_value_changed(self, func):
        """Register a function to be called each time a value of a device in this collection changed."""
        for device in self._devices.values():
            device.on_value_changed(func)


    def on_value_updated(self, func):
        """Register a function to be called each time a value of a device in this collection updated."""
        for device in self._devices.values():
            device.on_value_updated(func)



# FIXME: self.channels[0]: Provide better access to the channels. e.g. by names or ids or similar
class Device(Entity):
    _transform_attributes = {
        # ReGa attributes:
        #"id"                : int,
        #"deviceId"          : int,
        #"operateGroupOnly"  : lambda v: v != "false",

        # Low level attributes:
        "flags"             : int,
        "roaming"           : bool,
        "updateable"        : bool,
        "channels"          : Channel.from_channel_dicts,
    }

    # Don't add these keys to the objects attributes
    skip_attributes = [
        # Low level attributes:
        "children", # not needed
        "parent", # not needed
        "rf_address", # not available through XML-RPC and API, so exclude at all
        "rx_mode", # not available through XML-RPC and API, so exclude at all
    ]

    # These keys have to be set after attribute initialization
    _mandatory_attributes = [
        # Low level attributes:

        # Address of the device
        "address",
        # Firmware version string
        "firmware",
        # 0x01: show to user, 0x02 hide from user, 0x08 can not be deleted
        "flags",
        # serial number of the device
        "interface",
        # true when the device assignment is automatically adjusted
        "roaming",
        # device type
        "type",
        # true when an update is available
        "updatable",
        # version of the device description
        "version",
        # list of channel objects
        "channels",
    ]

    def __init__(self, api, spec):
        super(Device, self).__init__(api, spec)


    @classmethod
    def from_dict(self, api, spec):
        device_class = device_classes_by_type_name.get(spec["type"], Device)
        return device_class(api, spec)


    @classmethod
    def get_devices(self, api, **kwargs):
        return Devices(api).get(**kwargs)


    # {u'UNREACH': u'1', u'AES_KEY': u'1', u'UPDATE_PENDING': u'1', u'RSSI_PEER': u'-65535',
    #  u'LOWBAT': u'0', u'STICKY_UNREACH': u'1', u'DEVICE_IN_BOOTLOADER': u'0',
    #  u'CONFIG_PENDING': u'0', u'RSSI_DEVICE': u'-65535', u'DUTYCYCLE': u'0'}
    @property
    def maintenance(self):
        """Returns the whole set of all available maintenance parameters as dictionary."""
        return self.channels[0].values


    def set_logic_attributes(self, attrs):
        """Used to update the logic attributes of this device.

        Applying the attributes in the dictionary to this object. Special handling
        for some attributes which are already set by the low level attributes and
        for the channel attributes which are also part of attrs."""
        for channel_attrs in attrs["channels"]:
            self.channels[channel_attrs["index"]].set_logic_attributes(channel_attrs)

        # Skip non needed attributes (already set by low level data)
        attrs = attrs.copy()
        del attrs["channels"]
        del attrs["address"]
        del attrs["interface"]
        del attrs["type"]
        self._set_attributes(attrs)


    @property
    def is_online(self):
        """Returns True when the device is currently reachable. Otherwise False is returned."""
        if self.type == "HM-RCV-50":
            return True # CCU is always assumed to be online
        else:
            return not self.maintenance["UNREACH"].value


    @property
    def is_battery_low(self):
        """Returns True when the battery is reported to be low.

        When the battery is in normal state, False is returned. It might be a
        non battery powered device, then None is returned."""
        try:
            return self.maintenance["LOWBAT"].value
        except KeyError:
            return None # not battery powered


    @property
    def has_pending_config(self):
        if self.type == "HM-RCV-50":
            return False
        else:
            return self.maintenance["CONFIG_PENDING"].value


    @property
    def has_pending_update(self):
        try:
            return self.maintenance["UPDATE_PENDING"].value
        except KeyError:
            return False


    @property
    def rssi(self):
        return self.maintenance["RSSI_DEVICE"].value, self.maintenance["RSSI_PEER"].value


    def get_values(self):
        values = []
        for channel in self.channels:
            values.append(channel.get_values())
        return values


    def channel_by_address(self, address):
        """Returns the channel object having the requested address.

        When the device has no such channel, a ValueError() is raised.
        """
        for channel in self.channels:
            if address == channel.address:
                return channel
        raise KeyError("The channel could not be found on this device.")


    def summary_state(self, skip_channel_types=[]):
        """Returns a textual summary state of the device.

        Returns a string representing some kind of summary state of the device. This
        string does not necessarly contain all state information of the devices.

        When a device is unreachable, it does only return this information.

        This default method concatenates values and titles of channel values and
        returns them as string. The values are sorted by the titles."""
        formated = []

        if not self.is_online:
            return "The device is unreachable"

        if self.is_battery_low:
            formated.append("The battery is low")

        if self.has_pending_config:
            formated.append("Config pending")

        if self.has_pending_update:
            formated.append("Update pending")

        # FIXME: Add bad rssi?

        for channel in self.channels:
            if type(channel).__name__ not in skip_channel_types:
                txt = channel.summary_state()
                if txt != None:
                    formated.append(txt)

        if formated:
            return ", ".join(formated)
        else:
            return "Device reports no operational state"


    def on_value_changed(self, func):
        """Register a function to be called each time a value of this channel parameters has changed."""
        for channel in self.channels:
            channel.on_value_changed(func)


    def on_value_updated(self, func):
        """Register a function to be called each time a value of this channel parameters has updated."""
        for channel in self.channels:
            channel.on_value_updated(func)



class SpecificDevice(Device):
    @classmethod
    def get_all(self, API):
        return Device.get_devices(API, device_type=self.type_name)



# Funk-Heizkörperthermostat
class HMCCRTDN(SpecificDevice):
    type_name = "HM-CC-RT-DN"


# Virtuelle Fernbedienung der CCU
class HMRCV50(SpecificDevice):
    type_name = "HM-RCV-50"


# Funk-Tür-/ Fensterkontakt
class HMSecSC(SpecificDevice):
    type_name = "HM-Sec-SC"

    # Make methods of ChannelShutterContact() available
    def __getattr__(self, attr):
        return getattr(self.channels[1], attr)



# Funk-Schaltaktor mit Leistungsmessung
class HMESPMSw1Pl(SpecificDevice):
    type_name = "HM-ES-PMSw1-Pl"

    # Make methods of ChannelSwitch() available
    def __getattr__(self, attr):
        return getattr(self.channels[1], attr)


    def summary_state(self):
        return super(HMESPMSw1Pl, self).summary_state(
            skip_channel_types=["ChannelConditionPower", "ChannelConditionCurrent",
                                "ChannelConditionVoltage", "ChannelConditionFrequency"])



class HMPBI4FM(SpecificDevice):
    type_name = "HM-PBI-4-FM"

    def button(self, index):
        return self.channels[index+1]



class Rooms(object):
    """Manages a collection of rooms."""

    def __init__(self, api):
        super(Rooms, self).__init__()
        if not isinstance(api, pmatic.api.AbstractAPI):
            raise PMException("Invalid api object provided: %r" % api)
        self._api = api
        self._rooms = {}


    # FIXME: Add filter options
    def get(self):
        """Returns all room objects matching the provided filters.

        When the rooms have not been fetched yet, the room specs might be fetched
        from the CCU."""

        # Create new room group which is returned as result for this query
        rooms = Rooms(self._api)

        # FIXME: Cache this?
        for room_dict in self._api.room_get_all():
            # First create the room objects
            room = self._rooms.get(int(room_dict["id"]))
            if not room:
                room = Room(self._api, room_dict)

            # Now perform optional filtering

            self._rooms[room.id] = room
            rooms.add(room)
        return rooms


    def add(self, room):
        """Add a room object to the collection."""
        if not isinstance(room, Room):
            raise PMException("You can only add room objects.")
        self._rooms[room.id] = room


    # FIXME: Trigger spec fetch?
    def exists(self, room_id):
        """Check whether or not a room with the given id is in this collection."""
        return room_id in self._rooms


    # FIXME: Trigger spec fetch?
    def ids(self):
        """Returns a list of all addresses of all initialized room."""
        return self._rooms.keys()


    def delete(self, room_id):
        """Deletes the room with the given id from the pmatic runtime.

        The room is not deleted from the CCU.
        When the room is not known, the method is tollerating that."""
        try:
            del self._rooms[room_id]
        except KeyError:
            pass


    def clear(self):
        """Remove all objects from this room collection."""
        self._rooms.clear()


    # FIXME: Trigger spec fetch?
    def __iter__(self):
        for value in self._rooms.values():
            yield value


    def __len__(self):
        return len(self._rooms)



class Room(Entity):
    _transform_attributes = {
        "id"               : int,
        "channelIds"       : lambda x: list(map(int, x)),
    }

    def __init__(self, api, spec):
        self._values = {}
        self._devices = Devices(api)
        super(Room, self).__init__(api, spec)


    @classmethod
    def get_rooms(self, api):
        rooms = []
        for room_dict in api.room_get_all():
            rooms.append(Room(api, room_dict))
        return rooms


    @property
    def devices(self):
        """Returns list of device objects which have at least one channel associated with this room."""
        # FIXME: Cache this?
        return self._devices.get(has_channel_ids=self.channel_ids)


    @property
    def channels(self):
        """Returns list of channel objects associated with this room."""
        # FIXME: Cache this?
        room_channels = []
        for device in self._devices.get(has_channel_ids=self.channel_ids):
            for channel in device.channels:
                if channel.id in self.channel_ids:
                    room_channels.append(channel)
        return room_channels


    @property
    def programs(self):
        """Returns list of program objects which use at least one channel associated with this room."""
        # FIXME: Implement!
        # FIXME: Cache this?
        return []


    def add(self, channel_obj):
        """Adds a channel to this room."""
        # FIXME: Implement!


    def remove(self, channel_obj):
        """Removes a channel to this room."""
        # FIXME: Implement!


# Build a list of all specific product classes. If a device is initialized
# Device() checks whether or not a specific class or the generic Device()
# class should be used to initialize an object.
device_classes_by_type_name = {}
for key, val in list(globals().items()):
    if isinstance(val, type):
        if issubclass(val, Device) and key not in [ "Device", "SpecificDevice" ]:
            device_classes_by_type_name[val.type_name] = val

channel_classes_by_type_name = {}
for key, val in list(globals().items()):
    if isinstance(val, type):
        if issubclass(val, Channel) and key != "Channel":
            channel_classes_by_type_name[val.type_name] = val
