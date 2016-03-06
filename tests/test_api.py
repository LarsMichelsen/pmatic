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

from pmatic import PMException
import pmatic.utils as utils
import pmatic.api

def test_implicit_remote_init_missing_args():
    with pytest.raises(PMException):
        pmatic.api.init()


def test_explicit_remote_init_missing_args():
    with pytest.raises(PMException):
        pmatic.api.init("remote")


def test_explicit_local_init_but_remote():
    with pytest.raises(PMException):
        pmatic.api.init("local")


def test_explicit_local_enforce():
    orig_is_ccu = utils.is_ccu
    utils.is_ccu = lambda: True

    API = pmatic.api.init("local")
    assert isinstance(API, pmatic.api.LocalAPI)

    utils.is_ccu = orig_is_ccu


def test_explicit_wrong_init():
    with pytest.raises(PMException):
        pmatic.api.init("WTF?!")


class SpecificAPI(pmatic.api.AbstractAPI):
    def close(self):
        pass


class TestAbstractAPI(object):
    @pytest.fixture(scope="function")
    def API(self):
        return SpecificAPI()


    def test_invalid_response_handling(self, API, monkeypatch):
        with pytest.raises(PMException) as e:
            API._parse_api_response("ding", "{]")
        assert "Failed to parse response"

        def call_rega_present(method_name_int, **kwargs):
            if method_name_int == "rega_is_present":
                return True

        monkeypatch.setattr(API, "call", call_rega_present)
        with pytest.raises(PMException) as e:
           API._parse_api_response("dingdong",
              "{\"error\": {\"code\": 501, \"name\": \"xxx\", \"message\": \"asd\"}}")
        assert "[dingdong] xxx: asd" in str(e)

        def call_rega_not_present(method_name_int, **kwargs):
            if method_name_int == "rega_is_present":
                return False

        monkeypatch.setattr(API, "call", call_rega_not_present)
        with pytest.raises(PMException) as e:
           API._parse_api_response("dingdong",
              "{\"error\": {\"code\": 501, \"name\": \"xxx\", \"message\": \"asd\"}}")
        assert "the CCU has just been started" in str(e)


    def test_invalid_api_call(self, API, monkeypatch):
        def call(method_name_int, **kwargs):
            API._get_method(method_name_int)

        monkeypatch.setattr(API, "call", call)

        with pytest.raises(PMException) as e:
            API.dingdong_piff()
        assert "is not a valid method" in str(e)


    def test_del(self, API, monkeypatch):
        monkeypatch.setattr(API, "close", lambda: pmatic.api.AbstractAPI.close(API))
        with pytest.raises(NotImplementedError):
            API.__del__()


    def test_to_internal_name(self, API):
        assert API._to_internal_name("Interface.activateLinkParamset") \
                == "interface_activate_link_paramset"
        assert API._to_internal_name("DingReGaDong") \
                == "ding_rega_dong"
        assert API._to_internal_name("dingBidCoSDong") \
                == "ding_bidcos_dong"
        assert API._to_internal_name("ding.BidCoSDong") \
                == "ding_bidcos_dong"
        assert API._to_internal_name("Interface.setBidCoSInterface") \
                == "interface_set_bidcos_interface"


    def test_abstract_methods(self, API):
        with pytest.raises(NotImplementedError):
            API._get_methods_config()

        with pytest.raises(NotImplementedError):
            API.call("bla")

        with pytest.raises(NotImplementedError):
            super(SpecificAPI, API).close()
