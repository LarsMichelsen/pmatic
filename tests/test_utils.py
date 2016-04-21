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

import pytest
import sys
import platform
from pmatic import utils

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


from pmatic.exceptions import PMException

def test_is_string():
    assert utils.is_string("x")
    assert utils.is_string(1) == False
    assert utils.is_string(u"x")


def test_is_text():
    if sys.version_info[0] == 2:
        assert utils.is_text(str("x")) == False
    assert utils.is_text(1) == False
    assert utils.is_text(u"x") == True


def test_is_byte_string():
    assert utils.is_byte_string(bytes(b"X"))
    if sys.version_info[0] == 3:
        assert not utils.is_byte_string("X")
        assert utils.is_byte_string(b"X")
        assert utils.is_byte_string(bytes(b"X"))
    else:
        assert utils.is_byte_string(str("X"))
        assert not utils.is_byte_string("X")


def test_is_py2():
    if sys.version_info[0] == 2:
        assert utils.is_py2() == True
    else:
        assert utils.is_py2() == False

    saved = sys.version_info

    sys.version_info = [ 3, 1 ]
    assert utils.is_py2() == False
    sys.version_info = [ 2, 7 ]
    assert utils.is_py2() == True
    sys.version_info = [ 1, 0 ]
    assert utils.is_py2() == True
    sys.version_info = [ 4, 2 ]
    assert utils.is_py2() == False

    sys.version_info = saved


def test_decamel():
    assert utils.decamel("thisIsACamelCase") == "this_is_a_camel_case"
    assert utils.decamel("thisIsACamelCase") == "this_is_a_camel_case"
    assert utils.decamel('CamelCamelCase') == "camel_camel_case"
    assert utils.decamel('Camel2Camel2Case') == 'camel2_camel2_case'
    assert utils.decamel('getHTTPResponseCode') == 'get_http_response_code'
    assert utils.decamel('get2HTTPResponseCode') == 'get2_http_response_code'
    assert utils.decamel('HTTPResponseCode') == 'http_response_code'
    assert utils.decamel('HTTPResponseCodeXYZ') == 'http_response_code_xyz'


def test_fmt_temperature():
    assert utils.fmt_temperature(0.0) == "0.00 °C"
    assert utils.fmt_temperature(1) == "1.00 °C"
    assert utils.fmt_temperature(9.1234) == "9.12 °C"

    with pytest.raises(Exception):
        assert utils.fmt_temperature(None)

    with pytest.raises(Exception):
        assert utils.fmt_temperature("1.2")


def test_fmt_humidity():
    assert utils.fmt_humidity(0) == "0%"
    assert utils.fmt_humidity(199) == "199%"
    assert utils.fmt_humidity(1.2) == "1%"
    assert utils.fmt_humidity(1.6) == "1%"

    with pytest.raises(Exception):
        assert utils.fmt_humidity(None)


def test_fmt_percentage_int():
    assert utils.fmt_percentage_int(0) == "0%"
    assert utils.fmt_percentage_int(199) == "199%"
    assert utils.fmt_percentage_int(1.2) == "1%"
    assert utils.fmt_percentage_int(1.6) == "1%"

    with pytest.raises(Exception):
        assert utils.fmt_percentage_int(None)


def test_is_ccu(monkeypatch):
    def no_ccu_os_release(x):
        return StringIO(
            "PRETTY_NAME=\"Debian GNU/Linux 8 (jessie)\"\n"
            "NAME=\"Debian GNU/Linux\"\n"
            "VERSION_ID=\"8\"\n"
            "VERSION=\"8 (jessie)\"\n"
            "ID=debian\n"
            "HOME_URL=\"http://www.debian.org/\"\n"
            "SUPPORT_URL=\"http://www.debian.org/support/\"\n"
            "BUG_REPORT_URL=\"https://bugs.debian.org/\"\n"
        )

    def ccu_os_release(x):
        return StringIO(
            "NAME=Buildroot\n"
            "VERSION=2015.08.1\n"
            "ID=buildroot\n"
            "VERSION_ID=2015.08.1\n"
            "PRETTY_NAME=\"Buildroot 2015.08.1\""
        )

    def no_os_release(x):
        raise IOError("bla")

    monkeypatch.setattr(builtins, "open", no_os_release)
    monkeypatch.setattr(platform, "uname", lambda: (
        'Linux', 'dev', '3.16.0-4-amd64',
        '#1 SMP Debian 3.16.7-ckt9-3~deb8u1 (2015-04-24)', 'x86_64'))
    assert utils.is_ccu() == False

    monkeypatch.setattr(builtins, "open", no_ccu_os_release)
    monkeypatch.setattr(platform, "uname", lambda: (
        'Linux', 'dev', '3.16.0-4-amd64',
        '#1 SMP Debian 3.16.7-ckt9-3~deb8u1 (2015-04-24)', 'x86_64'))
    assert utils.is_ccu() == False

    monkeypatch.setattr(platform, "uname", lambda: (
        'Darwin', 'hubert.local', '11.4.2',
        'Darwin Kernel Version 11.4.2: Thu Aug 23 16:25:48 PDT 2012; '
        +'root:xnu-1699.32.7~1/RELEASE_X86_64', 'x86_64', 'i386'))
    assert utils.is_ccu() == False

    monkeypatch.setattr(platform, "uname", lambda: (
        'Windows', 'dhellmann', '2008ServerR2', '6.1.7600', 'AMD64',
        'Intel64 Family 6 Model 15 Stepping 11, GenuineIntel'))
    assert utils.is_ccu() == False

    monkeypatch.setattr(builtins, "open", ccu_os_release)
    monkeypatch.setattr(platform, "uname", lambda: (
        'Linux', 'dev', '3.16.0-4-amd64',
        '#1 SMP Debian 3.16.7-ckt9-3~deb8u1 (2015-04-24)', 'x86_64'))
    assert utils.is_ccu() == True

    monkeypatch.setattr(platform, "uname", lambda: (
        'Linux', 'ccu', '3.4.11.ccu2',
        '#1 PREEMPT Fri Oct 16 10:43:35 CEST 2015', 'armv5tejl'))
    assert utils.is_ccu() == True

    monkeypatch.setattr(platform, "uname", lambda: (
        'Linux', 'ccu2', '3.4.11.ccu2',
        '#1 PREEMPT Wed Dec 16 09:23:30 CET 2015', 'armv5tejl'))
    assert utils.is_ccu() == True


def test_is_manager_inline():
    assert utils.is_manager_inline() == False

    builtins.manager_ccu = True
    assert utils.is_manager_inline() == True


class TestPersistentStore(object):
    @pytest.fixture(scope="class")
    def store(self):
        return utils.PersistentStore()


    def test_name(self, store):
        assert store._name == None


    def test_load_not_existant(self, store):
        assert store._load("/asdas/ads/d") == None
        assert store._load("/asdas/ads/d", {}) == {}


    def test_load_empty_file(self, store, tmpdir):
        f = tmpdir.join("test_load_empty_file")
        f.open("w")
        path = "%s" % f
        with pytest.raises(PMException) as e:
            store._load(path)
        assert "Failed to load None:" in str(e)


    def test_load(self, store, tmpdir):
        f = tmpdir.join("testfile")
        f.write("{\"123\": \"234\"}")

        path = "%s" % f
        cfg = store._load(path)
        assert isinstance(cfg, dict)
        assert len(cfg) == 1
        assert cfg["123"] == "234"
