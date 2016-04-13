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

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:
    # Python 2.x
    import __builtin__ as builtins
except ImportError:
    # Python 3+
    import builtins

import pmatic
import pmatic.api
import pmatic.utils as utils
import lib
import pmatic.events

class TestCCU(lib.TestCCUClassWide):
    def test_manager_ccu_init(self, ccu):
        builtins.manager_ccu = ccu

        new_ccu = pmatic.CCU()
        assert new_ccu == ccu
        assert new_ccu.api == ccu.api
        assert isinstance(new_ccu.api, pmatic.api.AbstractAPI)

        del builtins.__dict__["manager_ccu"]
        assert not hasattr(builtins, "manager_ccu")

        new_ccu = pmatic.CCU()
        assert new_ccu != ccu


    def test_events_init(self, ccu):
        assert ccu._events == None
        assert isinstance(ccu.events, pmatic.events.EventListener)
        events = ccu.events
        assert events == ccu.events


    def test_interfaces(self, ccu):
        interfaces = ccu.interfaces
        assert isinstance(interfaces, list)
        assert len(interfaces) > 0
        assert isinstance(interfaces[0], dict)
        assert utils.is_string(interfaces[0]["info"])
        assert utils.is_string(interfaces[0]["name"])
        assert isinstance(interfaces[0]["port"], int)


    # FIXME: Fetch test files
    #def test_bidcos_interfaces(self, ccu):
    #    interfaces = ccu.bidcos_interfaces
    #    assert isinstance(interfaces, list)
    #    assert len(interfaces) > 0
    #    assert isinstance(interfaces[0], dict)
    #    assert utils.is_string(interfaces[0]["address"])
    #    assert utils.is_string(interfaces[0]["description"])
    #    assert isinstance(interfaces[0]["duty_cycle"], int)
    #    assert isinstance(interfaces[0]["is_connected"], bool)
    #    assert isinstance(interfaces[0]["is_default"], bool)


    # FIXME: Implement this
    #def test_signal_strengths(self, ccu):
    #    print(ccu.signal_strengths)
