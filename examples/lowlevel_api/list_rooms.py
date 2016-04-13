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

import pmatic.api

# Open up a remote connection via HTTP to the CCU and login as admin. When the connection
# can not be established within 5 seconds it raises an exception.
API = pmatic.api.init(
    # TODO: Replace this with the URL to your CCU2.
    address="http://192.168.1.26",
    # TODO: Insert your credentials here.
    credentials=("Admin", "EPIC-SECRET-PW"),
    connect_timeout=5
)

# Open a pmatic API locally on the CCU. You need to install a python environment on your CCU before.
# Please take a look at the documentation for details.
#API = pmatic.api.init()

for room_id in API.room_list_all():
    room_dict = API.room_get(id=room_id)
    # {u'description': u'Badezimmer', u'channelIds': [u'1977', u'1930', u'1433', u'1551', u'1554', u'1559'], u'id': u'1228', u'name': u'Bad'}
    print("%s (ID: %s, Description: %s)" % (room_dict["name"], room_id, room_dict["description"]))

API.close()
