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

try:
    from builtins import object # pylint:disable=redefined-builtin
except ImportError:
    pass

import os
import re
import sys
import logging

class LogMixin(object):
    """Inherit from this class to provide logging support.

    Makes a logger available via self.logger
    """
    _logger     = None
    _cls_logger = None

    @property
    def logger(self):
        if not self._logger:
            self._logger = logging.getLogger('.'.join([__name__, self.__class__.__name__]))
        return self._logger


    @classmethod
    def cls_logger(cls):
        if not cls._cls_logger:
            cls._cls_logger = logging.getLogger('.'.join([__name__, cls.__name__]))
        return cls._cls_logger



# Python 2/3 compatible string type check
def is_string(obj):
    if is_py2():
        return isinstance(obj, basestring) # noqa
    else:
        return isinstance(obj, str)


# Python 2/3 compatible check for unicode in 2 and str in 3.
def is_text(obj):
    if is_py2():
        return isinstance(obj, unicode) # noqa
    else:
        return isinstance(obj, str)


# Python 2/3 compatible check for non unicode (byte) string
def is_byte_string(obj):
    if is_py2():
        return isinstance(obj, str) # noqa
    else:
        return isinstance(obj, bytes)


def is_py2():
    """Returns True when executed with Python 2."""
    return sys.version_info[0] < 3


def decamel(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def fmt_temperature(temp):
    return "%0.2f °C" % temp


def fmt_humidity(hum):
    return "%d%%" % hum


def fmt_percentage_int(perc):
    return "%d%%" % perc


def is_ccu():
    """Returns True when executed on a CCU device. Otherwise False is being returned."""
    return ".ccu" in os.uname()[2]
