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

import os
import pytest

from pmatic.exceptions import PMUserError, PMException
import pmatic.notify
from pmatic.notify import Pushover

from lib import fake_urlopen, wrap_urlopen

@pytest.fixture(autouse=True)
def patch_urlopen(monkeypatch):
    if not is_testing_with_real_pushover():
        # First hook into urlopen to fake the HTTP responses
        monkeypatch.setattr(pmatic.notify, 'urlopen', fake_urlopen)
    else:
        # When executed with real ccu we wrap urlopen for enabling recording
        monkeypatch.setattr(pmatic.notify, 'urlopen', wrap_urlopen)


def is_testing_with_real_pushover():
    return os.environ.get("TEST_WITH_PUSHOVER") == "1"


def test_send_no_tokens():
    with pytest.raises(PMUserError) as e:
        Pushover.send("message")
    assert "api_token" in str(e)


def test_send_no_user_token():
    with pytest.raises(PMUserError) as e:
        Pushover.send("message", api_token="xxx")
    assert "user_token" in str(e)


def test_send_empty_message():
    with pytest.raises(PMUserError) as e:
        Pushover.send("", api_token="xxx", user_token="asd")
    assert "has to be specified" in str(e)


def test_send_too_long_message():
    with pytest.raises(PMUserError) as e:
        Pushover.send("x"*1025, api_token="xxx", user_token="asd")
    assert "exceeds" in str(e)

    with pytest.raises(PMException) as e:
        Pushover.send("x"*1024, api_token="xxx", user_token="asd")
    assert "status code: 400" in str(e)


def test_send_too_long_title():
    with pytest.raises(PMUserError) as e:
        Pushover.send("x", title="a"*251, api_token="xxx", user_token="asd")
    assert "exceeds" in str(e)

    with pytest.raises(PMException) as e:
        Pushover.send("x", title="a"*250, api_token="xxx", user_token="asd")
    assert "status code: 400" in str(e)


def test_send_invalid_message_type():
    with pytest.raises(PMUserError) as e:
        Pushover.send(b"x", api_token="xxx", user_token="asd")
    assert "unicode" in str(e)


def test_send_invalid_title_type():
    with pytest.raises(PMUserError) as e:
        Pushover.send("x", title=b"asd", api_token="xxx", user_token="asd")
    assert "unicode" in str(e)


def test_set_default_tokens():
    with pytest.raises(PMUserError) as e:
        Pushover.send("message")
    assert "api_token" in str(e)

    Pushover.set_default_tokens("asd", "xxx")
    with pytest.raises(PMException) as e:
        Pushover.send("message")
    assert "status code: 400" in str(e)


def test_send():
    assert Pushover.send("Hallo 123 :-)", api_token="Adrvcc6svnbFQ8hmAx5tDhbWU8nDK6",
                         user_token="go8cCpgmWMdm9j2jpm4TmdzuHpVUjh")
