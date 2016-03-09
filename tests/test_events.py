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
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import urlopen
    from urllib2 import HTTPError, URLError


import pmatic.events
from pmatic import PMException

import lib

class TestEventXMLRPCServer(object):
    @pytest.fixture(scope="class")
    def server(self):
        return pmatic.events.EventXMLRPCServer(("127.0.0.1", 9124))

    def test_system_list_methods(self, server):
        methods = server.system_listMethods("xxx")
        assert methods == ['system.listMethods',
                           'system.methodHelp',
                           'system.methodSignature',
                           'system.multicall']


    def test_execute(self, server):
        server.start()

        with pytest.raises(HTTPError) as e:
            urlopen("http://127.0.0.1:9124")
        assert "501: Unsupported method" in str(e)

        server.stop()

        socket.setdefaulttimeout(1)
        with pytest.raises(URLError):
            with pytest.raises(socket.timeout):
                urlopen("http://127.0.0.1:9124")


class TestEventListener(lib.TestCCU):
    def test_ident(self):
        pmatic.events.EventListener._ident = 0
        assert pmatic.events.EventListener._ident == 0
        assert pmatic.events.EventListener._next_id() == 0
        assert pmatic.events.EventListener._ident == 1
        assert pmatic.events.EventListener._next_id() == 1


    @pytest.fixture(scope="class")
    def listener(self, class_ccu):
        listener = pmatic.events.EventListener(class_ccu, ("127.0.0.1", 9124))
        assert listener._interface_id == "pmatic-%d" % (pmatic.events.EventListener._ident-1)
        assert listener.rpc_server_url == "http://127.0.0.1:9124"
        return listener


    def test_addresses(self, ccu):
        # listen all interfaces, 9123
        listener = pmatic.events.EventListener(ccu)
        assert listener._listen_address == ('', 9123)

        # Invalid listen address
        with pytest.raises(PMException) as e:
            listener = pmatic.events.EventListener(ccu, ('', ))
        assert "needs to be a tuple of two" in str(e)

        listener = pmatic.events.EventListener(ccu, listen_address=('', 1111))
        assert listener._listen_address == ('', 1111)

        listener = pmatic.events.EventListener(ccu, interface_id="bum!")
        assert listener._interface_id == "bum!"

        with pytest.raises(PMException) as e:
            listener = pmatic.events.EventListener(ccu, interface_id=True)
        assert "to be of type string" in str(e)


    def test_init(self, listener):
        assert listener.initialized == False
        listener.init()

        with pytest.raises(HTTPError) as e:
            urlopen("http://127.0.0.1:9124")
        assert "501: Unsupported method" in str(e)

        assert listener.initialized == True

        listener.close()
        assert listener.initialized == False

        socket.setdefaulttimeout(1)
        with pytest.raises(URLError):
            with pytest.raises(socket.timeout):
                urlopen("http://127.0.0.1:9124")


    def test_double_close(self, listener):
        listener.close()
        assert listener.initialized == False


    def test_wait(self, listener):
        assert listener.initialized == False
        listener.init()

        assert listener.wait(1) == True


    def test_rpc_server_url_detect(self, ccu, monkeypatch):
        listener = pmatic.events.EventListener(ccu, listen_address=("", 12345))

        class MySocket(socket.socket):
            def connect(self, address):
                return None

            def getsockname(self):
                return ("127.0.0.1", 9999)

            def close(self):
                return

        # Fake the address
        orig_address = ccu.api._address
        ccu.api._address = "http://127.0.0.1"
        monkeypatch.setattr(pmatic.events.socket, "socket", MySocket)

        assert listener.rpc_server_url == "http://127.0.0.1:12345"

        # Wrong - not reachable

        class MySocketConnectFail(socket.socket):
            def connect(self, address):
                raise socket.error("geht nicht")

        ccu.api._address = "http://169.254.1.2"
        socket.socket = MySocketConnectFail
        monkeypatch.setattr(pmatic.events.socket, "socket", MySocketConnectFail)
        with pytest.raises(PMException) as e:
            assert listener.rpc_server_url == "http://169.254.1.2:12345"
        assert "Unable to detect the address" in str(e)

        ccu.api._address = orig_address


    def test_get_callbacks(self, listener):
        assert listener._get_callbacks("value_updated") == []
        assert listener._get_callbacks("value_changed") == []

        with pytest.raises(PMException) as e:
            assert listener._get_callbacks("hauruck")
        assert "Invalid callback" in str(e)


    def test_remove_callback(self, listener):
        test = lambda: None

        # Don't raise when not registered yet
        listener.remove_callback("value_updated", test)
        assert listener._get_callbacks("value_updated") == []

        listener.register_callback("value_updated", test)
        assert test in listener._get_callbacks("value_updated")

        listener.remove_callback("value_updated", test)
        assert listener._get_callbacks("value_updated") == []

        with pytest.raises(PMException) as e:
            assert listener.remove_callback("hauruck", test)
        assert "Invalid callback" in str(e)


    def test_callback(self, listener):
        def add_element(liste):
            liste.append("hi")

        def raise_exc():
            raise Exception("GRÜN!")

        listener.register_callback("value_updated", add_element)
        test_list = []
        listener.callback("value_updated", test_list)
        assert len(test_list) == 1
        listener.remove_callback("value_updated", add_element)

        listener.register_callback("value_changed", raise_exc)
        with pytest.raises(Exception) as e:
            listener.callback("value_changed")
        assert "GRÜN!" in "%s" % e
        listener.remove_callback("value_changed", raise_exc)

        with pytest.raises(PMException) as e:
            assert listener.callback("hauruck")
        assert "Invalid callback" in str(e)


    def test_on_value_changed(self, listener):
        def add_element(liste):
            liste.append("hi")

        listener.on_value_changed(add_element)

        test_list = []
        listener.callback("value_changed", test_list)
        assert len(test_list) == 1
        listener.remove_callback("value_changed", add_element)


    def test_on_value_updated(self, listener):
        def add_element(liste):
            liste.append("ho")

        listener.on_value_updated(add_element)

        test_list = []
        listener.callback("value_updated", test_list)
        assert len(test_list) == 1
        listener.remove_callback("value_updated", add_element)


    # FIXME: test_wait()
