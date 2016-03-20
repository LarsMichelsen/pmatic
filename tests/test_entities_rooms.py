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
from pmatic.entities import Room, Rooms
from pmatic.ccu import CCURooms
from pmatic.exceptions import PMException

import lib

class TestRoom(lib.TestCCUClassWide):
    @pytest.fixture(scope="class")
    def room(self, ccu):
        assert isinstance(ccu.rooms, CCURooms)
        return list(ccu.rooms)[0]


    def test_attributes(self, room):
        assert isinstance(room, Room)

        assert isinstance(room.id, int)

        assert utils.is_text(room.name)
        room.name.encode("utf-8")

        assert utils.is_text(room.description)
        room.description.encode("utf-8")

        assert isinstance(room.channel_ids, list)
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



class TestCCURooms(lib.TestCCUClassWide):
    @pytest.fixture(scope="class")
    def rooms(self, ccu):
        return CCURooms(ccu)


    def test_ccu_devices_wrong_init(self):
        with pytest.raises(PMException):
            return CCURooms(None)


    def test_get_all(self, ccu, rooms):
        assert len(rooms._room_dict) == 0
        assert list(rooms) != []
        all_len = len(rooms)
        assert all_len > 0
        assert isinstance(rooms._room_dict, dict)
        assert len(rooms._room_dict) > 0

        result1 = ccu.rooms.query(room_name="Balkon")
        room = list(result1)[0]
        assert isinstance(room, Room)

        rooms.add(room)
        assert len(rooms) == all_len


    def test_query(self, ccu):
        rooms1 = ccu.rooms.query(room_name="Balkon")
        assert isinstance(rooms1, Rooms)
        assert len(list(rooms1)) == 1

        rooms2 = ccu.rooms.query(room_name="xxx")
        assert len(list(rooms2)) == 0

        rooms3 = ccu.rooms.query(room_name_regex="^Balkon$")
        assert len(list(rooms3)) == 1

        rooms4 = ccu.rooms.query(room_name_regex="^.*$")
        assert len(list(rooms4)) > 2


    def test_clear(self, rooms):
        assert len(rooms) > 0
        rooms.clear()
        assert len(rooms._room_dict) == 0



class TestRooms(lib.TestCCUClassWide):
    @pytest.fixture(scope="class")
    def rooms(self, ccu):
        return ccu.rooms.query()


    def test_get(self, rooms):
        first_id = list(rooms._rooms.keys())[0]
        assert isinstance(first_id, int)

        room = rooms.get(first_id)
        assert isinstance(room, Room)

        assert rooms.get(0) == None
        assert rooms.get(0, False) == False


    def test_add(self, rooms):
        with pytest.raises(PMException) as e:
            rooms.add(None)
        assert "Room objects" in str(e)

        first_room = list(rooms)[0]
        rooms.delete(first_room.id)
        assert not rooms.exists(first_room.id)

        rooms.add(first_room)
        assert rooms.exists(first_room.id)


    def test_ids(self, rooms):
        for id in rooms.ids:
            assert isinstance(id, int)

        assert len(rooms.ids) > 0
        assert len(rooms.ids) == len(rooms)


    def test_delete(self, rooms):
        # Deleting of not existing room does not raise an exception
        rooms.delete(0)


    def test_clear(self, rooms):
        assert len(rooms) > 0
        rooms.clear()
        assert len(rooms) == 0



