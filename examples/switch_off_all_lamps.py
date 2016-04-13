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

import pmatic

import sys

# Open up a remote connection via HTTP to the CCU and login as admin. When the connection
# can not be established within 5 seconds it raises an exception.
ccu = pmatic.CCU(
    address="http://192.168.1.26", # TODO: Replace this with the URL to your CCU2.
    credentials=("Admin", "EPIC-SECRET-PW"), # TODO: Insert your credentials here.
    connect_timeout=5
)

sys.stdout.write("Switching off all lamps...\n")

# Search all devices which contain the text "Lampe" in their name, then
# switch all of them off and report the result.
for device in ccu.devices.query(device_name_regex=".*Lampe.*"):
    sys.stdout.write("  %s..." % device.name)
    if device.switch_off():
        sys.stdout.write("done.\n")
    else:
        sys.stdout.write("failed!\n")

sys.stdout.write("Finished.\n")
