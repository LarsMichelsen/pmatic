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

from _pytest.monkeypatch import monkeypatch
import pytest

import os
import glob
#import logging
from hashlib import sha256
import json
import StringIO

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from pmatic import utils
import pmatic.api
from pmatic.api.remote import RemoteAPI

def request_id(url, data):
    data_hash = sha256(data).hexdigest()
    req = json.loads(data)
    return "%s_%s" % (req["method"], data_hash)


resources_path = "tests/resources"


def response_file_path(request_id):
    return "%s/%s.response" % (resources_path, request_id)


def status_file_path(request_id):
    return "%s/%s.status" % (resources_path, request_id)


def data_file_path(request_id):
    return "%s/%s.data" % (resources_path, request_id)


def fake_urlopen(url, data=None, timeout=None):
    """A stub urlopen() implementation that loads json responses from the filesystem.

    It first strips off the host part of the url and then uses the path info
    together with the post data to find a matching response. If no response has
    been recorded before, it raises an Exception() about the missing file.
    """

    rid = request_id(url, data)
    response = open(response_file_path(rid), "rb").read()
    http_status = int(open(status_file_path(rid), "rb").read())

    obj = StringIO.StringIO(response)
    obj.getcode = lambda: http_status

    return obj


def wrap_urlopen(url, data=None, timeout=None):
    """Wraps urlopen to record the response when communicating with a real CCU."""

    obj = urlopen(url, data=data, timeout=timeout)

    rid = request_id(url, data)

    if not os.path.exists(resources_path):
        os.makedirs(resources_path)

    open(response_file_path(rid), "wb").write(obj.read())
    open(status_file_path(rid), "wb").write(str(obj.getcode()))
    open(data_file_path(rid), "wb").write(data)

    return fake_urlopen(url, data, timeout)


def setup_module(module):
    """ When executed against a real CCU (recording mode), all existing
    resource files are deleted."""
    if is_testing_with_real_ccu():
        for f in glob.glob("tests/resources/*.data") \
               + glob.glob("tests/resources/*.status") \
               + glob.glob("tests/resources/*.response"):
            os.unlink(f)


def is_testing_with_real_ccu():
    return os.environ.get("TEST_WITH_CCU") == "1"


class TestRemoteAPI:
    @pytest.fixture(scope="class")
    def API(self, request):
        self.monkeypatch = monkeypatch()
        if not is_testing_with_real_ccu():
            # First hook into urlopen to fake the HTTP responses
            self.monkeypatch.setattr(pmatic.api.remote, 'urlopen', fake_urlopen)
        else:
            # When executed with real ccu we wrap urlopen for enabling recording
            self.monkeypatch.setattr(pmatic.api.remote, 'urlopen', wrap_urlopen)

        # FIXME: Make credentials configurable
        API = RemoteAPI(
            address="http://192.168.1.26",
            credentials=("Admin", "EPIC-SECRET-PW"),
            connect_timeout=5,
            #log_level=logging.DEBUG,
        )

        request.addfinalizer(lambda: API.close())

        return API


    def test_logged_in(self, API):
        assert len(API._session_id) == 10


    def test_methods_initialized(self, API):
        assert len(API._methods) > 10
        for method_name, method in API._methods.items():
            assert "INFO" in method
            assert "NAME" in method
            assert "LEVEL" in method
            assert "ARGUMENTS" in method
            assert "INT_ARGUMENTS" in method
            assert "SCRIPT_FILE" in method


    def test_Device_listAllDetail(self, API):
        devices = API.Device_listAllDetail()
        assert len(devices) > 10
        for device in devices:
            assert "id" in device
            assert "name" in device
            assert "channels" in device
            assert len(device["channels"]) > 0


    def test_Room_listAll(self, API):
        for room_id in API.Room_listAll():
            assert utils.is_text(room_id)


    def test_Room_get(self, API):
        first_room_id = API.Room_listAll()[0]
        room = API.Room_get(id=first_room_id)
        assert "name" in room
        assert "description" in room
        assert "channelIds" in room
        assert len(room["channelIds"]) > 0
