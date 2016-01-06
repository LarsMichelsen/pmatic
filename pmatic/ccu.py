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

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:
    # Is recommended for Python 3.x but fails on 2.7, but is not mandatory
    from builtins import object
except ImportError:
    pass

import time

from . import PMException


class CCU(object):
    def __init__(self, API):
        self.API  = API
        self.RSSI = None

    def interfaces(self):
        """Returns a list of available CCU interfaces.

        Example output:
            [ {u'info': u'BidCos-RF', u'name': u'BidCos-RF', u'port': 2001},
              {u'info': u'Virtual Devices', u'name': u'VirtualDevices', u'port': 9292} ]
        """
        return self.API.interface_list_interfaces()


    def bidcos_interfaces(self):
        """Returns a list of all BidCos interfaces of the CCU.

        Example output:
          [{u'address': u'KEQ0714972',
            u'description': u'',
            u'dutyCycle': u'0',
            u'isConnected': True,
            u'isDefault': True}]
        """
        return self.API.interface_list_bidcos_interfaces(interface="BidCos-RF")


    # Liefert eine Liste aller angelernten Geräte
    #API.interface_list_devices(interface="BidCos-RF"))


    def signal_strengths(self):
        if self.RSSI == None:
            self.RSSI = SignalStrength(self.API)
        return self.RSSI


# Fetches the signal strengt information about all connected devices
# from the CCU and caches these information for up to 360 seconds by
# default. The caching time can be set via constructor. Data can be
# accessed as in normal dicts.
class SignalStrength(dict):
    def __init__(self, API, max_cache_age=360):
        dict.__init__(self)
        self.API = API
        self._max_cache_age = max_cache_age # seconds
        self.update_data()


    def update_data(self):
        self.clear()
        for entry in self.API.interface_rssi_info(interface="BidCos-RF"):
            partner_dict = dict([(p["name"], p["rssiData"]) for p in entry["partner"] ])
            dict.__setitem__(self, entry["name"], partner_dict)
        self._last_update = time.time()


    def __getitem__(self, key):
        if self._last_update + self._max_cache_age < time.time():
            self.update_data()
        return dict.__getitem__(self, key)


    def __setitem__(self, key, val):
        raise PMException("Can not be changed.")


    def update(self, *args, **kwargs):
        raise PMException("Can not be changed.")
