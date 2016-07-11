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
This script computes the position of the sun in the sky, as seen from the
geographical location with the coordinates longitude (counted positive towards
East) and latitude (positive towards North). The position is computed for the
time when the function is called. It uses the Unix time stamp, provided by
the function time.time().
"""

from math import radians, degrees
from time import strftime, localtime

import pmatic.utils as utils

latitude = 50.5
longitude = 8.3

print("Computing the position of the sun for %0.1f degrees eastern longitude and %0.1f " \
      "degrees northern latitude.\n" % (longitude, latitude))

# Call sun_position with a fixed timestamp (corresponding to 07 Jul 2016 11:09:01 CEDT)
print("Date and time: Thu, 07 Jul 2016 11:09:01")
azimuth, altitude = utils.sun_position(radians(longitude), radians(latitude),
                                       unix_secs=1467882541.87)

# The expected output of the following print statement is:
# Azimut:  121.892834999 , Altitude:  50.597836317
print("Azimut: %r, Altitude: %r\n" % (degrees(azimuth), degrees(altitude)))

# Compute the sun's position for the current time
print(strftime("Date and time: %a, %d %b %Y %H:%M:%S", localtime()))

azimuth, altitude = utils.sun_position(radians(longitude), radians(latitude))

# The output of the following print statement is time-dependent and thus unknown in advance
print("Azimut: %r, Altitude: %r\n" % (degrees(azimuth), degrees(altitude)))
