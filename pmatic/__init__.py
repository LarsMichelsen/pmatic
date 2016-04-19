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

"""A simple to use API to the Homematic CCU

The pmatic module provides access to the Homematic CCU which operates as
the central unit in Homematic based home automation setips.. You can use
pmatic directly on the CCU2 or another system having Python installed.
With pmatic you can write your own Python scripts to communicate with
your CCU device.

Take a look at <https://github.com/LarsMichelsen/pmatic> for details.
"""

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__title__     = 'pmatic'
__version__   = "0.4"
__author__    = 'Lars Michelsen'
__license__   = 'GPLv2'
__copyright__ = 'Copyright 2016 Lars Michelsen'

import sys
import codecs
import logging as _logging

from pmatic.ccu import utils
from pmatic.ccu import CCU # noqa
from pmatic.exceptions import PMException, PMConnectionError, \
                              PMDeviceOffline, PMActionFailed, PMUserError # noqa

__all__ = [ "CCU", "logging",
            "PMException", "PMConnectionError", "PMDeviceOffline",
            "PMActionFailed", "PMUserError",
            "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG" ]

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

log_level_names = [
    "CRITICAL",
    "ERROR",
    "WARNING",
    "INFO",
    "DEBUG"
]

logger_default_handler = None

def logging(log_level=None):
    """Enables logging of pmatic log messages to stderr.

    When log_level is not set, it will default to WARNING if you did not
    configure the logging on your own in your application. Otherwise all log messages
    of pmatic which are of the given level or more severe will be logged to stderr.

    This is only a default to be used e.g. in simple scripts. If you need more
    flexible logging, you are free to configure the logging module on your own.
    """
    global logger_default_handler

    if log_level == None:
        log_level = WARNING

    logger.setLevel(log_level)

    # Remove eventual already existing default logger
    if logger_default_handler:
        logger.removeHandler(logger_default_handler)
        logger_default_handler = None

    # create console handler and set level to debug
    ch = _logging.StreamHandler()
    ch.setLevel(log_level)

    formatter = _logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)

    # add the stream handler to logger
    logger.addHandler(ch)
    logger_default_handler = ch


def fix_python2_pipe_encoding():
    """When using Python 2.7 and piping the output to a command like less or
    grep the sys.stdout/stderr encoding is not set correctly so printing the
    unicode strings will fail. Workaround this."""
    if utils.is_py2():
        if sys.stdout.encoding == None:
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout)
        if sys.stderr.encoding == None:
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr)


# Initialize logging with default log level (WARNING)
logging()

fix_python2_pipe_encoding()
