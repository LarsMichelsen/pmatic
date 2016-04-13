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

class PMException(Exception):
    """This is the base exception for all exceptions raised by pmatic.

    This exception is either a base class for all other pmatic specific
    exceptions but also directly raised in a lot of places where no more
    specific exception type exists.
    """
    pass


class PMConnectionError(PMException):
    """Is raised when the connection with the CCU could not be established.

    This exception is raised by pmatic.api in situations where the CCU could not
    be contacted. Normally such an exception means that the just failed action
    can be tried again later.

    For example when the CCU is currently not reachable this kind of exception
    is raised. Means it is worth it to try again later with same parameters.
    """
    pass


class PMDeviceOffline(PMException):
    """Is raised when trying to read e.g. values from the device but it is offline."""
    pass


class PMActionFailed(PMException):
    """Is raised when setting a value (parameter) of a channel fails."""
    pass


class SignalReceived(PMException):
    """Is used when a signal handler is registered to propagate the signal through the call stack.

    This is currently only used by the pmatic manager."""
    def __init__(self, signum):
        super(SignalReceived, self).__init__("Got signal %d" % signum)
        self._signum = signum


class PMUserError(PMException):
    """This exception is used when this situation is explicitly an error caused by the user.

    For example invalid user input in forms of the pmatic manager or similar."""
    pass
