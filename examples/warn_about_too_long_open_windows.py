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
Detect windows which are open longer than 15 minutes.

When executed on a regular base this script detects shutter contacts
(e.g. used for windows) that are open for more than 15 minutes.

The script prints out a warning message for each detected too long
open shutter contact.

You can easily adapt the script to warn faster and do anything else
instead of just printing a message.

This script might be executed on a regular base via cronjob. Another
option would be to slightly adapt the script to make it work in an
endless loop and checking open contacts in a configured interval.
"""

import time
import pmatic

ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

state_file   = "/tmp/window_states"
warn_seconds = 60 * 15 # > 15 minutes

try:
    states = eval(open(state_file, "rb").read())
except IOError:
    states = {} # initialize states

# Get all known HM-Sec-SC (shutter contact) devices
for device in ccu.devices.query(device_type="HM-Sec-SC"):
    if device.is_open:
        states.setdefault(device.id, time.time()) # store the first detected open time
        duration = time.time() - states[device.id]
        if duration > warn_seconds:
            # Instead of printing we can now send mails or whatever...
            print("WARNING: %s is open since %d Minutes" % (device.name, duration/60))

    elif device.id in states:
        del states[device.id] # closed -> delete open time

open(state_file, "wb").write(repr(states))
