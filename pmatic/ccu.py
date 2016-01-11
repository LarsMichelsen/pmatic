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

import pmatic.api
import pmatic.events
from pmatic.entities import Devices, Rooms


class CCU(object):
    """Defines the central object of more complex pmatic use cases.

    If you not only want to deal with states fetched from the CCU but also
    use them together with events received via the XML-RPC API of the CCU,
    the CCU object should be used as central manager.
    """
    def __init__(self, **kwargs):
        super(CCU, self).__init__()
        self.api = pmatic.api.init(**kwargs)
        self.rssi = None
        self._devices = None
        self._events = None
        self._rooms = None


    @property
    def devices(self):
        """Provides access to the collection of all known devices."""
        if not self._devices:
            self._devices = Devices(self.api)
        return self._devices


    @property
    def events(self):
        """Provides access to the pmatic XML-RPC EventListener instance."""
        if not self._events:
            self._events = pmatic.events.EventListener(self)
        return self._events


    @property
    def rooms(self):
        """Provides access to the collection of all known rooms."""
        if not self._rooms:
            self._rooms = Rooms(self.api)
        return self._rooms


    def interfaces(self):
        """Returns a list of available CCU communication interfaces.

        Example output:
            [ {u'info': u'BidCos-RF', u'name': u'BidCos-RF', u'port': 2001},
              {u'info': u'Virtual Devices', u'name': u'VirtualDevices', u'port': 9292} ]
        """
        return self.api.interface_list_interfaces()


    def bidcos_interfaces(self):
        """Returns a list of all BidCos interfaces of the CCU.

        Example output:
          [{u'address': u'KEQ0714972',
            u'description': u'',
            u'dutyCycle': u'0',
            u'isConnected': True,
            u'isDefault': True}]
        """
        return self.api.interface_list_bidcos_interfaces(interface="BidCos-RF")


    # FIXME: Consolidate API with self.devices.(...)
    def signal_strengths(self):
        if self.RSSI == None:
            self.RSSI = pmatic.api.SignalStrength(self.api)
        return self.RSSI
