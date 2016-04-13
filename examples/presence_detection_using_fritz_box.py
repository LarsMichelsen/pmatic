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

# Pmatic has a concept of persons and the presence of persons. For each
# person multiple devices can be configured which can then be used to
# detect the presence of a person. It is implemented as plugin mechanism
# which can be extended easily. For the start there is a plugin to control
# a persons availability by a device which is connected withe a fritz!Box
# in your local network.

import pmatic
ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

# Maybe you need to configure your fritz!Box credentials to be able to fetch the
# presence information of the configured devices.
from pmatic.residents import PersonalDeviceFritzBoxHost
PersonalDeviceFritzBoxHost.configure("fritz.box", password="EPIC-SECRET-PW")

# Now load some resident data.
ccu.residents.from_config({
    "residents": [
        {
            "id"             : 0,
            "name"           : "Lars",
            "email"          : "",
            "mobile"         : "",
            "pushover_token" : "",
            "devices": [
                {
                    "type_name": "fritz_box_host",
                    "mac": "30:10:E6:10:D4:B2",
                },
            ]
        }
    ],
})

# You may use ccu.residents.load(config_file="...") and the counterpart
# ccu.residents.load(config_file="...") to load and store your resident config.

# After initialization you can run either .update() on the residents instance
# or .update_presence() on a specific resident to update the presence information
# from the data source, in this case the fritz!Box.
ccu.residents.update()

for resident in ccu.residents.residents:
    #resident.update_presence()
    print(resident.name + " " + (resident.present and "is at home" or "is not at home"))
