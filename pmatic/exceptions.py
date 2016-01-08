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

class PMException(Exception):
    """This is the base exception for all exceptions raised by pmatic"""
    pass

class PMConnectionError(Exception):
    """Is raised when the connection with the CCU could not be established.

    This error is raised by pmatic.api in situations where the CCU could not
    be contacted. Normally such an exception means that the just failed action
    can be tried again later.

    For example when the CCU is currently not reachable this kind of exception
    is raised. Means it is worth it to try again later with same parameters.
    """

class PMActionFailed(PMException):
    pass

