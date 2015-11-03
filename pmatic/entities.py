#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - A simple API to to the Homematic CCU2
# Copyright (C) 2015 Lars Michelsen <lm@larsmichelsen.com>
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

import types
from . import utils, debug

class Entity(object):
    transform_attributes = {}

    def __init__(self, API, obj_dict):
        self.API = API
        self._init_from_detail_dict(obj_dict)


    def _init_from_detail_dict(self, obj_dict):
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
    @classmethod
    def from_channel_dicts(self, API, channel_dicts):
        channel_objects = []
        for channel_dict in channel_dicts:
            channel_class = channel_classes_by_type_name.get(channel_dict["channelType"], Channel)

            if channel_class == Channel:
                debug("Using generic Channel class (Type: %s): %r" % (channel_dict["channelType"], channel_dict))

            channel_objects.append(channel_class(API, channel_dict))
        return channel_objects


    def get_value(self, what=None):
        if self.is_readable:
            if what != None:
                id = "BidCos-RF.%s.%s" % (self.address, what)
            else:
                id = self.id

            return self.API.Channel_getValue(id=id)


    def formated_value(self):
        return "%s" % self.get_value()


class ChannelShutterContact(Channel):
    type_name = "SHUTTER_CONTACT"

    def get_value(self):
        raw_value = super(ChannelShutterContact, self).get_value()
        return raw_value != "false"


    def is_open(self):
        return self.get_value()


    def formated_value(self):
        return self.is_open() and "open" or "closed"


class ChannelSwitch(Channel):
    type_name = "SWITCH"

    def get_value(self):
        raw_value = super(ChannelSwitch, self).get_value()
        return raw_value != "false"


    def is_on(self):
        return self.get_value()


    def formated_value(self):
        return self.is_on() and "on" or "off"


class ChannelWeather(Channel):
    type_name = "WEATHER"

    def get_value(self):
        tmp = float(super(ChannelWeather, self).get_value("TEMPERATURE"))
        hum = float(super(ChannelWeather, self).get_value("HUMIDITY"))
        return tmp, hum


    def formated_value(self):
        hum, tmp = self.get_value()
        return "%s, %s" % (utils.fmt_temperature(tmp),
                           utils.fmt_humidity(hum))


class ChannelClimaVentDrive(Channel):
    type_name = "CLIMATECONTROL_VENT_DRIVE"

    def get_value(self):
        return int(super(ChannelClimaVentDrive, self).get_value())


    def formated_value(self):
        return utils.fmt_percentage_int(self.get_value())


class ChannelClimaRegulator(Channel):
    type_name = "CLIMATECONTROL_REGULATOR"

    def get_value(self):
        return float(super(ChannelClimaRegulator, self).get_value())


    def formated_value(self):
        val = self.get_value()
        if val == 0.0:
            return "Ventil closed"
        elif val == 100.0:
            return "Ventil open"
        else:
            return utils.fmt_temperature(val)


class Device(Entity):
    transform_attributes = {
        "id"               : (False, int),
        "deviceId"         : (False, int),
        "operateGroupOnly" : (False, lambda v: v != "false"),
        "channels"         : (True,  Channel.from_channel_dicts),
    }

    @classmethod
    def get_devices(self, API, device_type=None):
        devices = API.Device_listAllDetail()

        if type(device_type) in [str, unicode]:
            device_type = [device_type]

        device_objects = []
        for device_dict in devices:
            if device_type == None or device_dict["type"] in device_type:
                device_class = device_classes_by_type_name.get(device_dict["type"], Device)
                device_objects.append(device_class(API, device_dict))
        return device_objects


    def get_values(self):
        values = []
        for channel in self.channels:
            values.append(channel.get_value())
        return values


    def formated_value(self):
        formated = []
        for channel in self.channels:
            formated.append(channel.formated_value())
        return ", ".join(formated)


class SpecificDevice(Device):
    @classmethod
    def get_all(self, API):
        return Device.get_devices(API, device_type=self.type_name)


# Funk-Tür-/ Fensterkontakt
class HMSecSC(SpecificDevice):
    type_name = "HM-Sec-SC"


    def is_open(self):
        return self.channels[0].is_open()


    def formated_value(self):
        return self.channels[0].formated_value()


# Funk-Schaltaktor mit Leistungsmessung
class HMESPMSw1Pl(SpecificDevice):
    type_name = "HM-ES-PMSw1-Pl"




# Build a list of all specific product classes. If a device is initialized
# Device() checks whether or not a specific class or the generic Device()
# class should be used to initialize an object.
device_classes_by_type_name = {}
for key, val in globals().items():
    if isinstance(val, (type, types.ClassType)):
        if issubclass(val, Device) and key not in [ "Device", "SpecificDevice" ]:
                device_classes_by_type_name[val.type_name] = val

channel_classes_by_type_name = {}
for key, val in globals().items():
    if isinstance(val, (type, types.ClassType)):
        if issubclass(val, Channel) and key not in [ "Channel" ]:
                channel_classes_by_type_name[val.type_name] = val
