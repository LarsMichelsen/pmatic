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

try:
    from builtins import object # pylint:disable=redefined-builtin
except ImportError:
    pass

try:
    # Python 2.x
    import __builtin__ as builtins
except ImportError:
    # Python 3+
    import builtins

import os
import re
import sys
import json
import logging
import platform
import time
from math import sin, cos, pi, radians, atan2, asin, tan, log

from pmatic.exceptions import PMException


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



class CallbackMixin(object):
    """Manages callbacks which can be registered on an object inheriting from this class."""

    def __init__(self):
        self._callbacks = {}
        self._in_callbacks = []


    def _init_callbacks(self, cb_names):
        for cb_name in cb_names:
            self._callbacks[cb_name] = []


    def _get_callbacks(self, cb_name):
        try:
            return self._callbacks[cb_name]
        except KeyError:
            raise PMException("Invalid callback %s specified (Available: %s)" %
                                    (cb_name, ", ".join(self._callbacks.keys())))


    def register_callback(self, cb_name, func):
        """Register func to be executed as callback."""
        self._get_callbacks(cb_name).append(func)


    def remove_callback(self, cb_name, func):
        """Remove the specified callback func."""
        try:
            self._get_callbacks(cb_name).remove(func)
        except ValueError:
            pass # allow deletion of non registered function


    def _callback(self, cb_name, *args, **kwargs):
        """Execute all registered callbacks for this event.

        While the function is being processed, it reminds that the current callback is being
        executed. When another part of pmatic is trying to execut the exact same callback
        another time (may result in endless recursion), the second call is not executing the
        callbacks again. """
        if cb_name in self._in_callbacks:
            return # skip nested execution
        else:
            self._in_callbacks.append(cb_name)

        try:
            for callback in self._get_callbacks(cb_name):
                try:
                    callback(self, *args, **kwargs)
                except Exception as e:
                    raise PMException("Exception in callback (%s - %s): %s" % (cb_name, callback, e))
        finally:
            self._in_callbacks.remove(cb_name)



class PersistentStore(object):
    """This class provides the option to persist data structures in a file."""
    _name = None

    def _load(self, path, default=None):
        try:
            try:
                fh = open(path)
                data = json.load(fh)
            except IOError as e:
                # a non existing file is allowed.
                if e.errno == 2:
                    data = default
                else:
                    raise

            return data
        except Exception as e:
            raise PMException("Failed to load %s: %s" % (self._name, e))


    def _save(self, path, data):
        json_data = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        open(path, "w").write(json_data + "\n")



class PersistentConfigMixin(PersistentStore):
    def load_config(self, config_file=None, default=None):
        if config_file is None:
            config_file = self.config_file
        data = super(PersistentConfigMixin, self)._load(config_file, default=default)
        self.clear()
        self.from_config(data)


    def save_config(self, config_file=None):
        if config_file is None:
            config_file = self.config_file
        super(PersistentConfigMixin, self)._save(config_file, self.to_config())


    @property
    def config_file(self):
        raise NotImplementedError()


    def to_config(self):
        raise NotImplementedError()


    def from_config(self, config):
        raise NotImplementedError()



class PersistentStateMixin(PersistentStore):
    def load_state(self, state_file=None, default=None):
        if state_file is None:
            state_file = self.state_file
        data = super(PersistentStateMixin, self)._load(state_file, default=default)
        self.from_state(data)


    def save_state(self, state_file=None):
        if state_file is None:
            state_file = self.state_file
        super(PersistentStateMixin, self)._save(state_file, self.to_state())


    @property
    def state_file(self):
        raise NotImplementedError()


    def to_state(self):
        raise NotImplementedError()


    def from_state(self, state):
        raise NotImplementedError()



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
    if ".ccu" in platform.uname()[2]:
        return True

    try:
        for line in open("/etc/os-release"):
            if line == "NAME=Buildroot\n":
                return True
    except IOError:
        pass

    return False


def is_manager_inline():
    """Returns ``True`` when executed within the manager as inline script."""
    return hasattr(builtins, "manager_ccu")


def sun_position(longitude, latitude, unix_secs=0.):
    """
    Compute approximate values for azimuth and elevation angles of the sun.
    The azimuth is counted from North over East, South, and West.
    The maximum error is in the order of 1/100 degree. The precision is,
    therefore, more than sufficient for the purpose of home automation. The
    formula used for the elevation angle does not take atmospheric refraction
    into account. This leads to larger errors if the sun is close to the
    horizon, but it avoids a singularity.

    :param longitude: geographic longitude (radians) of the site.
    :param latitude: geographic latitude (radians) of the site.
    :param unix_secs: if not set to a value > 0., the current computer time
        is used. Otherwise, this value is interpreted as a Unix timestamp
        (counted in seconds since Jan. 1st, 1970, 0h UTC).
    :return: (azimuth, elevation), with azimuth and elevation angles in radians.
    """

    if unix_secs > 0.:
        t = unix_secs
    else:
        # t is the Unix timestamp, counted in seconds since Jan. 1st, 1970.
        t = time.time()

    # julian denotes the "Julian Date" used in astronomical formulae.
    julian = unix_timestamp_to_julian(t)

    # d denotes the number of days since epoch 2000.0.
    d = julian - 2451545.0

    # cap_t is the number of UTC hours since midnight.
    cap_t = ((julian - 0.5) % 1.) * 24.

    # cap_t0 is the number of centuries passed since epoch 2000.0.
    cap_t0 = (julian - cap_t / 24. - 2451545.0) / 36525.0
    l = radians(280.46 + 0.9856474 * d) % (2. * pi)
    g = radians(357.528 + 0.9856003 * d) % (2. * pi)
    cap_lambda = (l + radians(1.915 * sin(g) + 0.01997 * sin(2. * g))) % (
        2. * pi)

    # epsilon is the obliquity of the ecliptic.
    epsilon = radians(23.439 - 0.0000004 * d)

    # alpha, delta are the right ascension and declination angles of the sun.
    alpha = atan2(cos(epsilon) * sin(cap_lambda), cos(cap_lambda))
    delta = asin(sin(epsilon) * sin(cap_lambda))
    theta_g = radians(
        (6.697376 + 2400.05134 * cap_t0 + 1.002738 * cap_t) * 15.) % (2. * pi)

    # theta is the sidereal time at the site, tau the hour angle of the sun.
    theta = theta_g + longitude
    tau = theta - alpha

    azimuth = (atan2(sin(tau), cos(tau) * sin(latitude) - tan(delta) * cos(
        latitude)) + pi) % (2. * pi)
    elevation = asin(
        cos(delta) * cos(tau) * cos(latitude) + sin(delta) * sin(latitude))
    return (azimuth, elevation)


def unix_timestamp_to_julian(unix_secs):
    return (unix_secs / 86400.0) + 2440587.5


def dew_point(temperature, humidity):
    """
    Compute the temperature of the dew point, assuming an atmosphere without
    ice on the ground.

    :param temperature: ambient temperature in Celsius
    :param humidity: relative humidity (value between 0. and 1.)
    :return: temperature of the dew point in Celsius
    """

    k2, k3 = 17.62, 243.12

    dp = k3 * (k2 * temperature / (k3 + temperature) + log(humidity)) \
           / (k2 * k3 / (k3 + temperature) - log(humidity))

    return dp
