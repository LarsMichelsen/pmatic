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
import cgi
import time
import pytest
import signal
from bs4 import BeautifulSoup

import pmatic.manager
import pmatic.utils as utils
from pmatic.manager import Config, Html
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



class FieldStorageForTesting(cgi.FieldStorage):
    def setvalue(self, key, val):
        self.list.append(cgi.MiniFieldStorage(key, val))

    def clear(self):
        self.list = []



class HtmlForTesting(Html):
    def __init__(self):
        super(HtmlForTesting, self).__init__()
        self._vars = FieldStorageForTesting()
        self._page = []
        self.url = "/"


    def write(self, code):
        self._page.append(code)


    def flush(self):
        code = "".join(self._page)
        self._page = []
        return code


    def title(self):
        return "HtmlForTesting Title"



class TestHtml(object):
    @pytest.fixture(scope="function")
    def h(self):
        return HtmlForTesting()


    def test_is_action(self, h):
        assert h.is_action() == False
        h._vars.setvalue("action", "XY")
        assert h.is_action() == True


    def test_is_checked(self, h):
        assert h.is_checked("test123") == False
        h._vars.setvalue("test123", "1")
        assert h.is_checked("test123") == True
        h._vars.setvalue("test123", "")
        assert h.is_checked("test123") == True


    def test_add_missing_vars(self, h):
        h.add_missing_vars()
        assert h.flush() == ""

        h._vars.setvalue("dingeling", "1")
        h.add_missing_vars()
        page = h.flush()
        assert "<input type=\"hidden" in page
        assert "name=\"dingeling\"" in page


    def test_page_header_and_footer(self, h):
        h.page_header()
        h.page_footer()
        page = h.flush()
        bs = BeautifulSoup(page, "html.parser")
        assert len(bs.find_all("html")) == 1
        assert len(bs.find_all("head")) == 1
        assert len(bs.find_all("body")) == 1


    def test_navigation(self, h):
        h.navigation()
        page = h.flush()
        bs = BeautifulSoup(page, "html.parser")
        assert len(bs.find_all("ul")) == 1


    def test_begin_form(self, h):
        h._form_vars.append("xxx")
        assert "xxx" in h._form_vars
        h.begin_form()
        assert h._form_vars == []
        assert "<form " in h.flush()


    def test_end_form(self, h):
        h.end_form()
        assert "</form>" in h.flush()


    def test_upload(self, h):
        h.file_upload("upload", "text/plain")
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert len(soup.find_all("input")) == 1
        assert soup.find("input")["name"] == "upload"
        assert soup.find("input")["accept"] == "text/plain"
        assert "upload" in h._form_vars

        h.file_upload("upload")
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert soup.find("input")["accept"] == "text/*"


    def test_hidden(self, h):
        h.hidden("geheim", "blaah")
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert len(soup.find_all("input")) == 1
        assert soup.find("input")["type"] == "hidden"
        assert soup.find("input")["name"] == "geheim"
        assert "geheim" in h._form_vars


    def test_password(self, h):
        h.password("geheim")
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert len(soup.find_all("input")) == 1
        assert soup.find("input")["type"] == "password"
        assert soup.find("input")["name"] == "geheim"
        assert "geheim" in h._form_vars


    def test_submit(self, h):
        h.submit("Abschicken")
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert len(soup.find_all("button")) == 1
        assert soup.find("button")["type"] == "submit"
        assert soup.find("button")["name"] == "action"
        assert soup.find("button")["value"] == "1"
        assert "action" in h._form_vars

        h.submit("Abschicken", "xyz", "_action")
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert len(soup.find_all("button")) == 1
        assert soup.find("button")["type"] == "submit"
        assert soup.find("button")["name"] == "_action"
        assert soup.find("button")["value"] == "xyz"
        assert "action" in h._form_vars


    def test_input(self, h):
        h.input("text")
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert len(soup.find_all("input")) == 1
        assert soup.find("input")["type"] == "text"
        assert soup.find("input")["name"] == "text"
        assert soup.find("input")["value"] == ""
        assert "text" in h._form_vars

        h.input("text1", "hallo")
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert len(soup.find_all("input")) == 1
        assert soup.find("input")["type"] == "text"
        assert soup.find("input")["name"] == "text1"
        assert soup.find("input")["value"] == "hallo"
        assert "text1" in h._form_vars

        h.input("text2", "hallo", "cssclass")
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert len(soup.find_all("input")) == 1
        assert soup.find("input")["type"] == "text"
        assert soup.find("input")["name"] == "text2"
        assert soup.find("input")["value"] == "hallo"
        assert soup.find("input")["class"] == ["cssclass"]
        assert "text2" in h._form_vars


    def test_checkbox(self, h):
        h.checkbox("name")
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert len(soup.find_all("input")) == 1
        assert soup.find("input")["type"] == "checkbox"
        assert soup.find("input")["name"] == "name"
        assert "checked" not in soup.find("input")
        assert "name" in h._form_vars

        h.checkbox("name", True)
        soup = BeautifulSoup(h.flush(), "html.parser")
        assert len(soup.find_all("input")) == 1
        assert soup.find("input")["type"] == "checkbox"
        assert soup.find("input")["name"] == "name"
        assert soup.find("input")["checked"] == ""
        assert "name" in h._form_vars


    # FIXME: Add missing tests.


    def test_escape(self, h):
        result = h.escape("&\"'><")
        assert result == "&amp;&quot;&apos;&gt;&lt;"
        assert h.escape("<a href=\"'\">") == "&lt;a href=&quot;&apos;&quot;&gt;"
        assert h.escape(1) == "1"


    def test_write_text(self, h):
        h.write_text("<script>alert(1)</script>")
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in h.flush()
