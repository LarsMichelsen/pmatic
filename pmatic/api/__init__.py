#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - A simple API to to the Homematic CCU2
# Copyright (C) 2015 Lars Michelsen <lm@larsmichelsen.com>
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

import os

from .. import PMException
from .local import LocalAPI
from .remote import RemoteAPI

# Default API. It tries to detect whether or not this code is running on
# the CCU. If run on the CCU, it directly uses parts of the JSON API. When run
# from another system, it needs credentials and a URL to connect to.
def init(mode=None, **kwargs):
    if mode == None:
        mode = is_ccu() and "local" or "remote"

    if mode == "local":
        if not is_ccu():
            raise PMException("local mode can only be used on the CCU.")

        return LocalAPI(**kwargs)
    elif mode == "remote":
        try:
            return RemoteAPI(**kwargs)
        except TypeError, e:
            raise PMException("You need to provide at least the address and credentials "
                              "to access your CCU.")
    else:
        raise PMException("Invalid mode given. Valid ones are \"local\" and \"remote\".")


def is_ccu():
    return "ccu" in os.uname()
