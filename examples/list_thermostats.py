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

import pmatic
#pmatic.logging(pmatic.DEBUG)

ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

for device in ccu.devices.query(device_type="HM-CC-RT-DN"):
    # You can use the generic summary_state() method.
    print("%s: %s" % (device.name, device.summary_state))

    # But you can also use the individual attributes
    print("%s:" % device.name)
    print("  is disabled:     %s" % device.is_off)
    print("  control mode:    %s" % device.control_mode)
    print("  temperature:     %0.2f" % device.temperature)
    print("  set temperature: %0.2f" % device.set_temperature)
    print("")
