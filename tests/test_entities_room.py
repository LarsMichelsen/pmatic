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

import pmatic.utils as utils
from pmatic.entities import Room
from pmatic.ccu import CCURooms

import lib

class TestRoom(lib.TestCCU):
    @pytest.fixture(scope="function")
    def room(self, ccu):
        assert type(ccu.rooms) == CCURooms
        return list(ccu.rooms)[0]


    def test_attributes(self, room):
        assert isinstance(room, Room)

        assert isinstance(room.id, int)

        assert utils.is_text(room.name)
        room.name.encode("utf-8")

        assert utils.is_text(room.description)
        room.description.encode("utf-8")

        assert type(room.channel_ids) == list
        for channel_id in room.channel_ids:
            assert isinstance(channel_id, int)


    def test_devices(self, room):
        for device in room.devices:
            has_room_channel = False
            for channel in device.channels:
                if channel.id in room.channel_ids:
                    has_room_channel = True
                    break

            assert has_room_channel


    def test_channels(self, room):
        channels = room.channels
        assert len(channels) == len(room.channel_ids)

        for channel in channels:
            assert channel.id in room.channel_ids
