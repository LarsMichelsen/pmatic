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

import sys
import logging
import itertools
import pmatic.api

##
# Opening a pmatic session
##

# Open up a remote connection via HTTP to the CCU and login as admin. When the connection
# can not be established within 5 seconds it raises an exception.
API = pmatic.api.init(
    address="http://192.168.1.26",
    credentials=("Admin", "EPIC SECRET PW"),
    connect_timeout=5,
    #log_level=logging.DEBUG
)

# Open a pmatic API locally on the CCU. You need to install a python environment on your CCU before.
# Please take a look at the documentation for details.
#API = pmatic.api.init()

# An example room dict:
# {u'channelIds': [u'1874', u'1495'],
#  u'description': u'',
#  u'id': u'1224',
#  u'name': u'Schlafzimmer'}
devices = API.Device_listAllDetail()

line_fmt = "%-30s %s"

# Print the header
print(line_fmt % ("Name", "State"))
print(line_fmt % ("-" * 30, "-" * 6))

# Loop all devices, only care about shutter contacts
for device in devices:
    if device["type"] == "HM-Sec-SC":
        # Get the channel of the shutter contact and then fetch the state
        channel = [ c for c in device["channels"] if c["channelType"] == "SHUTTER_CONTACT" ][0]
        is_open = API.Channel_getValue(id=channel["id"]) == "true"

        print(line_fmt % (device["name"], is_open and "OPEN" or "CLOSED"))

API.close()
