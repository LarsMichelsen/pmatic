#!/usr/bin/python
# encoding: utf-8

# http://www.eq-3.de/Downloads/Software/HM-CCU2-Firmware_Updates/Tutorials/hm_devices_Endkunden.pdf

import sys
import pmatic.api

##
# Opening a pmatic session
##

# Open up a remote connection via HTTP to the CCU and login as admin. When the connection
# can not be established within 5 seconds it raises an exception.
API = pmatic.api.init(
    address="http://192.168.1.26",
    credentials=("Admin", "dingeling:-)"),
    connect_timeout=5
)

# Open a pmatic API locally on the CCU. You need to install a python environment on your CCU before.
# Please take a look at the documentation for details.
#API = pmatic.api.init()

##
# API Examples
##

# Print all methods including their arguments and description which is available on your device
#API.print_methods()

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

# FIXME: Was ist Interface.init?

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

# {u'channelIds': [u'1874', u'1495'],
#  u'description': u'',
#  u'id': u'1224',
#  u'name': u'Schlafzimmer'}
rooms = API.Room_getAll()
#for room in rooms:
#    print room["name"], room["channelIds"]

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
            print device["name"], repr(channel["id"]), is_open

            # FIXME: Multiple rooms?
            room = [ r for r in rooms if channel["id"] in r["channelIds"] ][0]
            if not room:
                raise Exception("Found window contact without room")

            room_humidity = avg_rel_humidity_of_room(room["id"])
            room_temperature = avg_temperature_of_room(room["id"])

            if room_humidity:
                print "Humidity:", room_humidity, "%"
            if room_temperature:
                print "Temperature:", room_temperature, "C"

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

            print "Outside:", outside_rel_humidity(), "%", out_temp, "C"

# List room ids
#for room in API.Room_listAll():
#    pprint.pprint(room)

# FIXME: Implement API own methods:
# Channel_getNameById(id=...)
# Channel_listRoomIds(id=...)

# FIXME:
# API.Room("1234")
# for room in API.getAllRooms():
#     print room.id
#     for channel in room.channels():
#         print channel.id
#         print channel.getValue()

# FIXME:
# for device in API.getAllDevices():
#    print device.name

#if not API.Event_subscribe():
#    raise Exception("Failed to subscribe to events.")
#while True:
#    result = API.Event_poll()
#    if result:
#        print result
#print API.Event_unsubscribe()

API.close()
