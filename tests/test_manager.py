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

import os
import time
import pytest
import signal

import pmatic.manager
from pmatic.exceptions import SignalReceived

class TestConditionOnTime(object):
    @pytest.fixture(scope="class")
    def manager(self):
        return None # FIXME: Return manager object


    @pytest.fixture(scope="function")
    def c(self, manager):
        return pmatic.manager.ConditionOnTime(manager)


    def _time(self, timetxt):
        return time.mktime(time.strptime(timetxt, "%Y-%m-%d %H:%M:%S"))


    def _fake_time(self, monkeypatch, timetxt):
        monkeypatch.setattr(pmatic.manager.time, "time",
                lambda: self._time(timetxt))


    def test_daily(self, c, monkeypatch):
        c.interval_type = "daily"
        c.time_of_day   = (9, 0)

        assert c._next_time == None

        self._fake_time(monkeypatch, "2016-09-22 08:59:59")
        assert c.next_time == self._time("2016-09-22 09:00:00")

        self._fake_time(monkeypatch, "2016-09-22 09:00:00")
        c.calculate_next_time()
        assert c.next_time == self._time("2016-09-23 09:00:00")

        self._fake_time(monkeypatch, "2016-09-22 09:00:01")
        c.calculate_next_time()
        assert c.next_time == self._time("2016-09-23 09:00:00")

        self._fake_time(monkeypatch, "2016-09-23 00:00:00")
        c.calculate_next_time()
        assert c.next_time == self._time("2016-09-23 09:00:00")

        self._fake_time(monkeypatch, "2016-09-22 23:59:59")
        c.calculate_next_time()
        assert c.next_time == self._time("2016-09-23 09:00:00")

        self._fake_time(monkeypatch, "2016-12-31 23:59:59")
        c.calculate_next_time()
        assert c.next_time == self._time("2017-01-01 09:00:00")


    def test_weekly(self, c, monkeypatch):
        c.interval_type = "weekly"
        c.day_of_week   = 1 # monday
        c.time_of_day   = (19, 31)

        assert c._next_time == None

        self._fake_time(monkeypatch, "2016-09-22 08:59:59") # thursday
        assert c.next_time == self._time("2016-09-26 19:31:00")

        self._fake_time(monkeypatch, "2016-09-19 00:00:00") # monday
        c.calculate_next_time()
        assert c.next_time == self._time("2016-09-19 19:31:00")

        self._fake_time(monkeypatch, "2016-12-31 23:59:00") # saturday
        c.calculate_next_time()
        assert c.next_time == self._time("2017-01-02 19:31:00")


    def test_monthly(self, c, monkeypatch):
        c.interval_type = "monthly"
        c.day_of_month   = 1
        c.time_of_day   = (00, 00)

        assert c._next_time == None

        self._fake_time(monkeypatch, "2016-09-22 08:59:59")
        assert c.next_time == self._time("2016-10-01 00:00:00")

        self._fake_time(monkeypatch, "2016-01-30 23:59:59")
        c.calculate_next_time()
        assert c.next_time == self._time("2016-02-01 00:00:00")

        self._fake_time(monkeypatch, "2016-11-01 00:00:00")
        c.calculate_next_time()
        assert c.next_time == self._time("2016-12-01 00:00:00")

        self._fake_time(monkeypatch, "2016-12-31 23:59:59")
        c.calculate_next_time()
        assert c.next_time == self._time("2017-01-01 00:00:00")

        self._fake_time(monkeypatch, "2016-02-29 11:11:11")
        c.calculate_next_time()
        assert c.next_time == self._time("2016-03-01 00:00:00")



class TestManager(object):
    @pytest.fixture(scope="function")
    def manager(self, monkeypatch):
        monkeypatch.setattr(pmatic.api, 'init', lambda **kwargs: None)
        return pmatic.manager.Manager(("127.0.0.1", 1337))



    # FIXME: Also test SIGINT, SIGQUIT
    def test_signal_handler(self, manager):
        manager.register_signal_handlers()

        with pytest.raises(SignalReceived) as e:
            c = 10
            os.system("kill -TERM %d" % os.getpid())
            while c > 0:
                time.sleep(1)
                c -= 1

        assert e.value._signum == signal.SIGTERM
