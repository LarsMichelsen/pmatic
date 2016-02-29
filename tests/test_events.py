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

import pytest
import socket

try:
    from urllib.request import urlopen
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen
    from urllib2 import HTTPError


import pmatic.events

class TestEventXMLRPCServer(object):
    @pytest.fixture(scope="class")
    def server(self):
        return pmatic.events.EventXMLRPCServer(("127.0.0.1", 9123))

    def test_system_list_methods(self, server):
        methods = server.system_listMethods("xxx")
        assert methods == ['system.listMethods',
                           'system.methodHelp',
                           'system.methodSignature',
                           'system.multicall']


    def test_execute(self, server):
        server.start()

        try:
            urlopen("http://127.0.0.1:9123")
        except HTTPError as e:
            assert "Unsupported method" in e.reason
            assert e.code == 501

        server.stop()

        socket.setdefaulttimeout(1)
        with pytest.raises(socket.timeout):
            urlopen("http://127.0.0.1:9123")

