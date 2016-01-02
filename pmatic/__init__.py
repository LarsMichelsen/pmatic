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

import logging

VERSION = "0.1"

class PMException(Exception):
    pass

#
# Logging
#

logger_name = "pmatic"
logger      = None


def init_logger(log_level=None):
    global logger
    if not logger:
        logger = logging.getLogger(logger_name)
        if log_level != None:
            logger.setLevel(log_level)

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        if log_level != None:
            ch.setLevel(log_level)
        # create formatter
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        # add formatter to ch
        ch.setFormatter(formatter)

        # add ch to logger
        logger.addHandler(ch)

    return logger


def log(*args):
    if not logger:
        init_logger()
    return logger.log(*args)


def debug(*args):
    if not logger:
        init_logger()
    return logger.debug(*args)
