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
import pmatic.utils as utils
from pmatic.manager import Config
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


class TestConfig(object):
    def test_default_config(self):
        config_options = [
            "config_path",
            "static_path",
            "script_path",
            "ccu_enabled",
            "ccu_address",
            "ccu_credentials",
            "log_level",
            "log_file",
            "event_history_length",
            "pushover_api_token",
            "pushover_user_token",
        ]

        for key in Config.__dict__.keys():
            if key not in [ "__module__", "__doc__", "load", "save", "_config_path" ]:
                assert key in config_options

        for key in config_options:
            assert hasattr(Config, key)

    def test_load(self, tmpdir, capfd):
        pmatic.logging()

        p = tmpdir.join("manager.config")

        class TestConfig(Config):
            @classmethod
            def _config_path(cls):
                return "%s" % p.realpath()

        # Load empty config -> it's ok
        TestConfig.load()

        # Load invalid config. Check error handling
        p.write("asdasd")
        with pytest.raises(SystemExit):
            TestConfig.load()

        out, err = capfd.readouterr()
        assert "Failed to load the config. Terminating." in err
        assert out == ""

        # Load empty json construct
        p.write("{}", mode="w")
        TestConfig.load()

        # Load empty json construct
        p.write("{\"log_level\": 10}", mode="w")
        TestConfig.load()
        assert TestConfig.log_level == 10


    def test_load_io_errors(self, capfd):
        pmatic.logging()

        # IOError - some error code
        class TestConfigIOError1(Config):
            @classmethod
            def _config_path(cls):
                raise IOError()

        with pytest.raises(SystemExit):
            TestConfigIOError1.load()
        out, err = capfd.readouterr()
        assert "Failed to load the config. Terminating." in err
        assert out == ""

        # non existing file is ok
        class TestConfigIOError2(Config):
            @classmethod
            def _config_path(cls):
                e = IOError()
                e.errno = 2
                raise e

        TestConfigIOError2.load()


    def test_save(self, tmpdir):
        p = tmpdir.join("manager.config")

        class TestConfig(Config):
            @classmethod
            def _config_path(cls):
                return "%s" % p.realpath()

        # Save empty config
        TestConfig.save()
        assert p.read() == "{}\n"

        # don't save empty attributes
        TestConfig._hidden_attr = 1
        TestConfig.save()
        assert p.read() == "{}\n"

        # don't save internal attributes
        TestConfig.config_path = "xy"
        TestConfig.script_path = "xy"
        TestConfig.static_path = "xy"
        TestConfig.log_file    = "xy"
        TestConfig.save()
        assert p.read() == "{}\n"

        # don't try to save internal attributes
        TestConfig.test_config_val = "xy"
        TestConfig.save()
        assert p.read() == "{\"test_config_val\": \"xy\"}\n"


    def test_config_path(self):
        path = Config._config_path()
        assert utils.is_text(path)
        assert path.endswith("manager.config")
