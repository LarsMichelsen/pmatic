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

"""A simple API to to the Homematic CCU2

pmatic is a python library to provide access to the Homematic CCU2. You
can execute pmatic directly on the CCU2 or another system having Python
installed. With pmatic you can write your own Python scripts to communicate
with your CCU2 devices.

Take a look at <https://github.com/LaMi-/pmatic> for details.

:copyright: (c) 2016 by Lars Michelsen.
:license: GNU General Public License v2, see LICENSE for more details.
"""

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__title__     = 'pmatic'
__version__   = '2.4.3'
__author__    = 'Lars Michelsen'
__license__   = 'GPLv2'
__copyright__ = 'Copyright 2016 Lars Michelsen'

import logging as _logging

from pmatic.ccu import CCU
from pmatic.exceptions import *

#
# Logging
#

# Set default logging handler to avoid "No handler found" warnings.
try:
    # Python 2.7+
    from _logging import NullHandler
except ImportError:
    class NullHandler(_logging.Handler):
        def emit(self, record):
            pass


logger = _logging.getLogger(__name__)
logger.addHandler(NullHandler())

# Users should be able to set log levels without importing "logging"
CRITICAL = _logging.CRITICAL
ERROR    = _logging.ERROR
WARNING  = _logging.WARNING
INFO     = _logging.INFO
DEBUG    = _logging.DEBUG


def logging(log_level=None):
    """Enables logging of pmatic log messages to stderr.

    When nothing log_level is not set, it will default to WARNING if you did not
    configure the logging on your own in your application. Otherwise all log messages
    of pmatic which are of the given level or more severe will be logged to stderr.

    This is only a default to be used e.g. in simple scripts. If you need more
    flexible logging, you are free to configure the logging module on your own.
    """
    if log_level != None:
        logger.setLevel(log_level)

    # create console handler and set level to debug
    ch = _logging.StreamHandler()
    if log_level != None:
        ch.setLevel(log_level)

    formatter = _logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)

    # add the stream handler to logger
    logger.addHandler(ch)
