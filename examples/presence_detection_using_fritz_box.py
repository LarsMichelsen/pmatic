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

# Pmatic has a concept of persons and the presence of persons. For each
# person multiple devices can be configured which can then be used to
# detect the presence of a person. It is implemented as plugin mechanism
# which can be extended easily. For the start there is a plugin to control
# a persons availability by a device which is connected withe a fritz!Box
# in your local network.

from pmatic.presence import Presence

# Basic configuration for the connection with your fritz!Box.
# Other available parameters are port=49000, user="username".
from pmatic.presence import PersonalDeviceFritzBoxHost
PersonalDeviceFritzBoxHost.configure("fritz.box", password="EPIC-SECRET-PW")

# Now create a presence manager instance and configure it. Currently the easiest
# way is to use it is to use the from_config() method with the following data:
p = Presence()
p.from_config({
    "persons": [
        {
            "name": "Lars",
            "devices" : [
                {
                    "type_name": "fritz_box_host",
                    "mac": "30:10:E6:10:D4:B2",
                },
            ]
        }
    ],
})

# After initialization you can run either .update() on the presence instance
# or .update_presence() on a specific person to update the presence information
# from the data source, in this case the fritz!Box.
p.update()

for person in p.persons:
    #person.update_presence()
    print(person.name + " " + (person.present and "is at home" or "is not at home"))
