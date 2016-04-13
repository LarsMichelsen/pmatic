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

"""
Simply prints out all temperatures reported by the devices of type
HM-CC-TC, HM-WDS10-TH-O and HM-CC-RT-DN.

This script is executed until terminated by the user (e.g. via CTRL+C).
It listens for incoming events and prints a message to the user once
the a temperature update is received.

This detection is using the events sent by the CCU. So the state
updates are printed nearly instantly.
"""

import pmatic

ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))
devices = ccu.devices.query(device_type=["HM-CC-TC", "HM-WDS10-TH-O", "HM-CC-RT-DN"])

# This function is executed on each state change
def print_summary_state(param):
    print("%s %s" % (param.channel.device.name, param.channel.summary_state))

devices.on_value_updated(print_summary_state)

if not devices:
    print("Found no devices. Terminating.")
else:
    print("Waiting for changes...")

    ccu.events.init()
    ccu.events.wait()
    ccu.events.close()
