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

"""Provides the API interface to the CCU

This module provides you with the low level API of pmatic to the CCU2.
Low level API means that it cares about connecting to the interfaces on
the CCU, authenticates with it and accesses the API calls and makes them
all available in the Python code. So that you can simply call methods on
the API object to make API calls and get Python data structures back.

The most important function of this module is the init() function. This
is the function you should call in your program code to initialize the
API object. It detects whether or not the code is run on the CCU or
a remote connection from another system is made to the CCU.
"""

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from .. import PMException
from .local import LocalAPI
from .remote import RemoteAPI

def init(mode=None, **kwargs):
    """Wrapper to create the API object you need to acces the CCU API.

    By default it detects whether or not this code is being executed on the CCU
    or on another system. And initializes either a LocalAPI() object when run
    directly on a CCU or, in all other cases, a RemoteAPI() object. This object
    is then being returned.

    You can provide the mode argument to disable auto detection and either set
    it to "local" to enforce a LocalAPI() object to be created or "remote" to
    enforce a RemoteAPI() object.

    In case a RemoteAPI() object is being created, you need to provide at least
    the additional keyword arguments address="http://[HOST]" which needs to
    contain the base URL to your CCU together with credentials=("[USER]", "PASSWORD")
    which must be valid credentials to authenticate with the CCU.
    """
    if mode == None:
        mode = is_ccu() and "local" or "remote"

    if mode == "local":
        if not is_ccu():
            raise PMException("local mode can only be used on the CCU.")

        return LocalAPI(**kwargs)
    elif mode == "remote":
        try:
            return RemoteAPI(**kwargs)
        except TypeError as e:
            raise PMException("You need to provide at least the address and credentials "
                              "to access your CCU (%s)." % e)
    else:
        raise PMException("Invalid mode given. Valid ones are \"local\" and \"remote\".")


def is_ccu():
    """Returns True when executed on a CCU device. Otherwise False is being returned."""
    return "ccu" in os.uname()
