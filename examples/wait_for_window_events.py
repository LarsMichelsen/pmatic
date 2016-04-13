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
Detect state changes of shutter contacts and warn about them.

This script is executed until terminated by the user (e.g. via CTRL+C).
It listens for incoming events and prints a message to the user once
the state change is detected.

This detection is using the events sent by the CCU. So the state
changes are detected nearly instantly.

The script prints out a warning message for each detected too long
open shutter contact. You can easily adapt the script to do anything else
instead of just printing a message.
"""

import time
import pmatic
#pmatic.logging(pmatic.DEBUG)

ccu = pmatic.CCU(
    address="http://192.168.1.26",
    credentials=("Admin", "EPIC-SECRET-PW"),
    connect_timeout=5,
)

# Get all HM-Sec-SC (shutter contact) devices
devices = ccu.devices.query(device_type="HM-Sec-SC")

# This function is executed on each state change
def print_summary_state(param):
    # Format the time of last change for printing
    last_changed = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(param.last_changed))
    print("%s %s %s" % (last_changed, param.channel.device.name, param.channel.summary_state))

# Register event handler for all grouped devices. It is possible to register to device
# specific events like on_closed and on_opend or generic events like on_value_changed:
#devices.on_opend(print_summary_state)
#devices.on_closed(print_summary_state)
devices.on_value_changed(print_summary_state)
#devices.on_value_updated(print_summary_state)

num_sensors = len(devices)
if not num_sensors:
    print("Found no shutter contact sensors. Terminating.")
else:
    print("Found %d shutter contact sensors. Waiting for changes..." % num_sensors)

    ccu.events.init()

    # Now wait for changes till termination of the program
    ccu.events.wait()
    ccu.events.close()
