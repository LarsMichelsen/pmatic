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
# - http://www.eq-3.de/Downloads/PDFs/Dokumentation_und_Tutorials/HM_Script_Teil_4_Datenpunkte_1_503.pdf

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

try:
    # Is recommended for Python 3.x but fails on 2.7, but is not mandatory
    from builtins import object
except ImportError:
    pass

from . import utils, debug, warning, params

class Entity(object):
    transform_attributes = {}

    def __init__(self, API, obj_dict):
        self.API = API
        self._init_attributes(obj_dict)


    def _init_attributes(self, obj_dict):
        for key, val in obj_dict.items():
            # Optionally convert values using the given transform functions
            # for the specific object type
            trans = self.transform_attributes.get(key)
            if trans:
                add_api_obj, trans_func = trans
                if add_api_obj:
                    val = trans_func(self.API, val)
                else:
                    val = trans_func(val)

            # Transform keys from camel case to our style
            key = utils.decamel(key)

            setattr(self, key, val)


class Channel(Entity):
    def __init__(self, *args, **kwargs):
        self._values = {}
        super(Channel, self).__init__(*args, **kwargs)


    @classmethod
    def from_channel_dicts(self, API, channel_dicts):
        channel_objects = []
        for channel_dict in channel_dicts:
            channel_class = channel_classes_by_type_name.get(channel_dict["channelType"], Channel)

            if channel_class == Channel:
                debug("Using generic Channel class (Type: %s): %r" % (channel_dict["channelType"], channel_dict))

            channel_objects.append(channel_class(API, channel_dict))
        return channel_objects


    def _fetch_values(self):
        """Fetches all values of the channel.

        Gathers the values of the channel including their specifications. From this data
        parameter objects are constructed which are added to self._values of the Channel.
        """
        raw_values = self.API.interface_get_paramset(interface="BidCos-RF", address=self.address, paramsetKey="VALUES")

        self._values.clear()
        for param_spec in self.API.interface_get_paramset_description(interface="BidCos-RF", address=self.address, paramsetType="VALUES"):
            param_id = param_spec["ID"]

            class_name = "Parameter%s" % param_spec["TYPE"]
            cls = getattr(params, class_name)
            if not cls:
                warning("%s: Skipping unknown parameter %s of type %s. Class %s not implemented." %
                                              (self.channel_type, param_id, param_spec["TYPE"], class_name))
            else:
                self._values[param_id] = cls(self, param_spec, raw_values.get(param_id))


    @property
    def values(self):
        # FIXME: Update every access? Add some caching?
        self._fetch_values()
        return self._values


    def formated_values(self):
        # FIXME: Order?
        formated = []
        for value in self._values:
            formated.append(value.formated())
        return ", ".join(formated)



# FIXME: Handle LOWBAT/ERROR
class ChannelShutterContact(Channel):
    type_name = "SHUTTER_CONTACT"

    def is_open(self):
        return self.values["STATE"] == "1"


    def formated_values(self):
        return self.is_open() and "open" or "closed"



# FIXME: Handle INHIBIT, WORKING
class ChannelSwitch(Channel):
    type_name = "SWITCH"

    def is_on(self):
        return self.values["STATE"]


    def formated_values(self):
        return self.is_on() and "on" or "off"


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



# FIXME: Handle all values:
# {u'POWER': u'3.520000', u'ENERGY_COUNTER': u'501.400000', u'BOOT': u'1',
#  u'CURRENT': u'26.000000', u'FREQUENCY': u'50.010000', u'VOLTAGE': u'228.900000'}
class ChannelPowermeter(Channel):
    type_name = "POWERMETER"

    def formated_values(self):
        values = self.values
        return "Power: %(POWER)0.2f Wh, Voltage: %(VOLTAGE)0.2f V, " \
               "Energy-Counter: %(ENERGY_COUNTER)0.2f Wh, " \
               "Current: %(CURRENT)0.2f mA, " \
               "Frequency: %(FREQUENCY)0.2f Hz" % values


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


class ChannelWeather(Channel):
    type_name = "WEATHER"

    def formated_values(self):
        return "%s, %s" % (utils.fmt_temperature(self.values["TEMPERATURE"]),
                           utils.fmt_humidity(self.values["HUMIDITY"]))



# FIXME: Handle ERROR
class ChannelClimaVentDrive(Channel):
    type_name = "CLIMATECONTROL_VENT_DRIVE"

    def formated_values(self):
        return utils.fmt_percentage_int(self.values["VALVE_STATE"])



# FIXME: Handle ADJUSTING_COMMAND, ADJUSTING_DATA
class ChannelClimaRegulator(Channel):
    type_name = "CLIMATECONTROL_REGULATOR"

    def formated_values(self):
        val = self.values["SETPOINT"]
        if val == 0.0:
            return "Ventil closed"
        elif val == 100.0:
            return "Ventil open"
        else:
            return utils.fmt_temperature()


# Devices:
#  HM-CC-RT-DN
# FIXME: Values:
# {u'SET_TEMPERATURE': u'21.500000', u'PARTY_START_MONTH': u'1', u'BATTERY_STATE': u'2.400000', u'PARTY_START_DAY': u'1', u'PARTY_STOP_DAY': u'1', u'PARTY_START_YEAR': u'0', u'FAULT_REPORTING': u'0', u'PARTY_STOP_TIME': u'0', u'ACTUAL_TEMPERATURE': u'23.100000', u'BOOST_STATE': u'15', u'PARTY_STOP_YEAR': u'0', u'PARTY_STOP_MONTH': u'1', u'VALVE_STATE': u'10', u'PARTY_START_TIME': u'450', u'PARTY_TEMPERATURE': u'5.000000', u'CONTROL_MODE': u'1'}
class ChannelClimaRTTransceiver(Channel):
    type_name = "CLIMATECONTROL_RT_TRANSCEIVER"

    def formated_values(self):
        return "%s (Target: %s)" % (utils.fmt_temperature(self.values["ACTUAL_TEMPERATURE"]),
                                    utils.fmt_temperature(self.values["SET_TEMPERATURE"]))



# Has not any values
class ChannelWindowSwitchReceiver(Channel):
    type_name = "WINDOW_SWITCH_RECEIVER"


# Has not any values
class ChannelWeatherReceiver(Channel):
    type_name = "WEATHER_RECEIVER"


# Devices:
#  HM-CC-RT-DN
# Has not any values
class ClimateControlReceiver(Channel):
    type_name = "CLIMATECONTROL_RECEIVER"


# Devices:
#  HM-CC-RT-DN
# Has not any values
class ClimateControlRTReceiver(Channel):
    type_name = "CLIMATECONTROL_RT_RECEIVER"


# Devices:
#  HM-CC-RT-DN
# Has not any values
class RemoteControlReceiver(Channel):
    type_name = "REMOTECONTROL_RECEIVER"


class Device(Entity):
    transform_attributes = {
        "id"               : (False, int),
        "deviceId"         : (False, int),
        "operateGroupOnly" : (False, lambda v: v != "false"),
        "channels"         : (True,  Channel.from_channel_dicts),
    }

    @classmethod
    def get_devices(self, API, device_type=None, device_name=None, device_name_regex=None):
        devices = API.device_list_all_detail()

        if utils.is_string(device_type):
            device_type = [device_type]

        device_objects = []
        for device_dict in devices:
            if device_type != None and device_dict["type"] not in device_type:
                continue

            # Exact match device name
            if device_name != None and device_name != device_dict["name"]:
                continue

            # regex match device name
            if device_name_regex != None and not re.match(device_name_regex, device_dict["name"]):
                continue

            device_class = device_classes_by_type_name.get(device_dict["type"], Device)
            device_objects.append(device_class(API, device_dict))
        return device_objects


    # {u'UNREACH': u'1', u'AES_KEY': u'1', u'UPDATE_PENDING': u'1', u'RSSI_PEER': u'-65535',
    #  u'LOWBAT': u'0', u'STICKY_UNREACH': u'1', u'DEVICE_IN_BOOTLOADER': u'0',
    #  u'CONFIG_PENDING': u'0', u'RSSI_DEVICE': u'-65535', u'DUTYCYCLE': u'0'}
    # FIXME: Cache this
    def get_maintenance(self, what=None):
        values = self.API.interface_get_paramset(interface="BidCos-RF", address=self.address + ":0", paramsetKey="VALUES")
        return values


    def online(self):
        if self.type == "HM-RCV-50":
            return True # CCU is always assumed to be online
        else:
            return self.get_maintenance()["UNREACH"] == "0"


    def battery_low(self):
        try:
            return self.get_maintenance()["LOWBAT"] == "1"
        except KeyError:
            return None # not battery powered


    def has_pending_config(self):
        return self.get_maintenance()["CONFIG_PENDING"] == "1"


    def has_pending_update(self):
        return self.get_maintenance()["UPDATE_PENDING"] == "1"


    def rssi(self):
        info = self.get_maintenance()
        return info["RSSI_DEVICE"], info["RSSI_PEER"]


    def get_values(self):
        values = []
        for channel in self.channels:
            values.append(channel.get_values())
        return values


    def formated_values(self):
        formated = []
        for channel in self.channels:
            formated.append(channel.formated_values())
        return ", ".join(formated)



class SpecificDevice(Device):
    @classmethod
    def get_all(self, API):
        return Device.get_devices(API, device_type=self.type_name)



# Funk-Tür-/ Fensterkontakt
class HMSecSC(SpecificDevice):
    type_name = "HM-Sec-SC"

    # Make methods of ChannelShutterContact() available
    def __getattr__(self, attr):
        return getattr(self.channels[0], attr)


# Funk-Schaltaktor mit Leistungsmessung
class HMESPMSw1Pl(SpecificDevice):
    type_name = "HM-ES-PMSw1-Pl"

    # Make methods of ChannelSwitch() available
    def __getattr__(self, attr):
        return getattr(self.channels[0], attr)


class HMPBI4FM(SpecificDevice):
    type_name = "HM-PBI-4-FM"

    def button(self, index):
        return self.channels[index]


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
