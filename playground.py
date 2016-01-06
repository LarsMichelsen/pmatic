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

# http://www.eq-3.de/Downloads/PDFs/Dokumentation_und_Tutorials/HM_XmlRpc_V1_502__2_.pdf
# http://www.eq-3.de/Downloads/Software/HM-CCU2-Firmware_Updates/Tutorials/hm_devices_Endkunden.pdf
# https://sites.google.com/site/homematicplayground/api/json-rpc

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys, pprint
import pmatic.api
import pmatic.events
from pmatic.entities import *
from pmatic import utils
from pmatic.ccu import CCU

##
# Opening a pmatic session
##

# Open up a remote connection via HTTP to the CCU and login as admin. When the connection
# can not be established within 5 seconds it raises an exception.
API = pmatic.api.init(
    address="http://192.168.1.26",
    credentials=("Admin", "EPIC-SECRET-PW"),
    connect_timeout=5,
    log_level=pmatic.DEBUG,
)

# Register with the XML-RPC API of the CCU, then wait until program termination
# for event and print them to the console.
#events = pmatic.events.init(API, listen_address=('192.168.1.36', 9123))
events = pmatic.events.init(API)
events.init()
events.wait()
events.close()

sys.exit(1)

#CCU = CCU(API)
#print(CCU.interfaces())

# Event-Methoden scheinen nicht so zu funktionieren, wie gedacht. Hier kommen jedenfalls keine Events an.
#print(API.event_subscribe())
#
#while True:
#    result = API.event_poll()
#    if result:
#        print(result)
#
#print(API.event_unsubscribe())

#
#for device in Device.get_devices(API, device_name="Büro-Lampe"):
#    for channel in device.channels:
#        print(device.name, channel.get_values())
#        print(device.name, channel.channel_type, channel.name, channel.formated_values())

for device in Device.get_devices(API):
    if not device.online():
        print("OFFLINE:", device.name)
    else:
        for channel in device.channels:
            if channel.__class__ == Channel:
                print("", device.name, channel.channel_type, channel.name, channel.summary_state())
                print(channel.values)
            else:
                print(device.name, channel.channel_type, channel.name, channel.summary_state())
                print(channel.values)
                for name, v in channel.values.items():
                    print(name, v.datatype)

sys.exit(1)

##
# API Examples
##


# Executes a homematic script and prints "HI THERE" (the output) of the script
#print API.ReGa_runScript(script="Write(\"HI THERE\")")

#print API.call("Room.listAll")
#print API.call("CCU.getSSHState")
#print API.call("system.listMethods")
#print API.call("system.describe")

#for room_id in API.Room_listAll():
#    room_dict = API.Room_get(id=room_id)
#    # {u'description': u'Badezimmer', u'channelIds': [u'1977', u'1930', u'1433', u'1551', u'1554', u'1559'], u'id': u'1228', u'name': u'Bad'}
#    for channel_id in room_dict["channelIds"]:
#        print "Channel ID:", channel_id, "Value:", API.Channel_getValue(id=channel_id)

import pprint


def Device_listDetailByType(ty):
    device = []
    for device in API.Device_listAllDetail():
        #  {u'address': u'KEQ0163218',
        #  u'channels': [{u'address': u'KEQ0163218:1',
        #                 u'category': u'CATEGORY_SENDER',
        #                 u'channelType': u'SHUTTER_CONTACT',
        #                 u'deviceId': u'1753',
        #                 u'id': u'1774',
        #                 u'index': 1,
        #                 u'isAesAvailable': True,
        #                 u'isEventable': True,
        #                 u'isLogable': True,
        #                 u'isLogged': True,
        #                 u'isReadable': True,
        #                 u'isReady': True,
        #                 u'isUsable': True,
        #                 u'isVirtual': False,
        #                 u'isVisible': True,
        #                 u'isWritable': False,
        #                 u'mode': u'MODE_AES',
        #                 u'name': u'B\xfcro-Fenster',
        #                 u'partnerId': u''}],
        #  u'id': u'1753',
        #  u'interface': u'BidCos-RF',
        #  u'name': u'B\xfcro-Fenster',
        #  u'operateGroupOnly': u'false',
        #  u'type': u'HM-Sec-SC'}
        # pprint.pprint(device)
        if device["type"] == ty:
            devices.append(device)
    return devices

#for device in devices:
#    print device["id"], device["name"]
#    for c in device["channels"]:
#        #{u'category': u'CATEGORY_SENDER', u'index': 1, u'isReady': True, u'isEventable': True, u'name': u'Balkon-Sensor', u'isVirtual': False, u'isWritable': False, u'isVisible': True, u'isLogable': True, u'partnerId': u'', u'deviceId': u'1306', u'isReadable': True, u'address': u'KEQ0174549:1', u'isAesAvailable': False, u'isUsable': True, u'isLogged': True, u'channelType': u'WEATHER', u'id': u'1326', u'mode': u'MODE_DEFAULT'}
#        #print "  ", channel["name"], channel["channelType"], channel["category"], API.Channel_getValue(id=channel["id"])
#        if c["channelType"] == "WEATHER":
#            print "  ", c["name"], "Temp:", API.Channel_getValue(id="BidCos-RF."+c["address"]+".TEMPERATURE"), \
#                  "Humidity:", API.Channel_getValue(id="BidCos-RF."+c["address"]+".HUMIDITY")
#            sys.exit(1)


devices = API.Device_listAllDetail()
import itertools
channels = list(itertools.chain.from_iterable([ d["channels"] for d in devices ]))

def channels_of_room(room_id):
    room = [ r for r in rooms if r["id"] == room_id ][0]
    return [ c for c in channels if c["id"] in room["channelIds"] ]


def avg_of_room(room_id, what):
    val = None
    for c in channels_of_room(room_id):
        if c["channelType"] == "WEATHER":
            this_val = float(API.Channel_getValue(id="BidCos-RF."+c["address"]+"."+what))

        elif c["channelType"] == "CLIMATECONTROL_RT_TRANSCEIVER" and what == "TEMPERATURE":
            this_val = float(API.Channel_getValue(id="BidCos-RF."+c["address"]+".ACTUAL_TEMPERATURE"))

        #elif c["category"] == "CATEGORY_SENDER":
        #    print c["name"], c["channelType"]
        #    continue

        else:
            continue

        if val == None:
            val = this_val
        else:
            val = (val + this_val) / 2
    return val


def avg_rel_humidity_of_room(room_id):
    return avg_of_room(room_id, "HUMIDITY")


def avg_temperature_of_room(room_id):
    return avg_of_room(room_id, "TEMPERATURE")


def outside_rel_humidity():
    outside_room = [ r for r in rooms if r["name"] == "Balkon" ][0]
    return avg_rel_humidity_of_room(outside_room["id"])


def outside_temperature():
    outside_room = [ r for r in rooms if r["name"] == "Balkon" ][0]
    return avg_temperature_of_room(outside_room["id"])


for device in devices:
    if device["type"] == "HM-Sec-SC":
        channel = [ c for c in device["channels"] if c["channelType"] == "SHUTTER_CONTACT" ][0]
        is_open = API.Channel_getValue(id=channel["id"])

        if True: #is_open:
            print((device["name"], repr(channel["id"]), is_open))

            # FIXME: Multiple rooms?
            room = [ r for r in rooms if channel["id"] in r["channelIds"] ][0]
            if not room:
                raise Exception("Found window contact without room")

            room_humidity = avg_rel_humidity_of_room(room["id"])
            room_temperature = avg_temperature_of_room(room["id"])

            if room_humidity:
                print(("Humidity:", room_humidity, "%"))
            if room_temperature:
                print(("Temperature:", room_temperature, "C"))

            if room_humidity and room_humidity > 70:
                pass # lüften!

            if room_temperature and room_temperature < 20:
                pass # fenster zu!

            out_temp = outside_temperature()
            if out_temp > 19:
                pass # wurst, lüfte halt
            elif out_temp > 15:
                pass # 30 minuten
            elif out_temp > 5:
                pass # 15 minuten
            else:
                pass # 10 minuten

            print(("Outside:", outside_rel_humidity(), "%", out_temp, "C"))


API.close()
