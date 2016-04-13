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

"""I use this script to let the pmatic Manager inform me once a week about
all devices which are found to have a low battery level. To archieve this
I created a schedule which is executed once a week which executes the
script inline. This is important to be able to use the resident information
of the pmatic Manager."""

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys, traceback

import pmatic
from pmatic.notify import Pushover
from pmatic.manager import Config

if not pmatic.utils.is_manager_inline():
    print("This script can only be called from the pmatic Manager as inline script.")
    sys.exit(0)

ccu = pmatic.CCU()

# Create a list of all devices having a low battery
low = []
for device in ccu.devices:
    if device.is_battery_low:
        low.append(device.name)

if not low:
    print("All battery powered devices are fine.")
    sys.exit(0)


print("Found low batteries: %s" % ", ".join(low))

# Load the resident to inform
lars = ccu.residents.get_by_name("Lars")
if lars is None:
    print("Failed to load resident \"Lars\".")
    sys.exit(1)

if not lars.pushover_token:
    print("Lars has no pushover token configured. Terminating.")
    sys.exit(1)

if not Config.pushover_api_token:
    print("There is no API token configured in the manager. Terminating.")
    sys.exit(1)

if len(low) == 1:
    title = "1 device has low batteries"
else:
    title = "%d devices have low batteries" % len(low)

try:
    Pushover.send("Low batteries: %s" % ", ".join(low), title,
              api_token=Config.pushover_api_token,
              user_token=lars.pushover_token)
except:
    print(traceback.format_exc())
