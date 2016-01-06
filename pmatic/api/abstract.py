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

"""An abstract implementation of the pmatic low level API."""

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import sys
import atexit

try:
    # Is recommended for Python 3.x but fails on 2.7, but is not mandatory
    from builtins import object
except ImportError:
    pass

from .. import PMException, PMConnectionError, init_logger, utils

class AbstractAPI(object):
    """An abstract implementation of the pmatic low level API.

    This is the base class for all specific API classes, which are currently
    LocalAPI() and RemoteAPI().
    """
    def __init__(self, logger, log_level):
        self._methods = {}
        self._init_logger(logger, log_level)


    def _register_atexit_handler(self):
        """Can be called to register a cleanup handler on interpreter exit.

        The APIs can register this to ensures the close() method is called
        on interpreter shutdown."""
        atexit.register(self.close)


    def _init_logger(self, logger, log_level):
        """Initializes the logger of this object."""
        if logger == None:
            self._logger = init_logger(log_level)
        else:
            self._logger = logger


    def logger(self):
        """Returns the logger object used by this object."""
        return self._logger


    def debug(self, *args, **kwargs):
        """Log a message with severity 'DEBUG' on this objects logger."""
        self._logger.debug(*args, **kwargs)


    def info(self, *args, **kwargs):
        """Log a message with severity 'INFO' on this objects logger."""
        self._logger.info(*args, **kwargs)


    def warning(self, *args, **kwargs):
        """Log a message with severity 'WARNING' on this objects logger."""
        self._logger.warning(*args, **kwargs)


    def error(self, *args, **kwargs):
        """Log a message with severity 'ERROR' on this objects logger."""
        self._logger.error(*args, **kwargs)


    def critical(self, *args, **kwargs):
        """Log a message with severity 'CRITICAL' on this objects logger."""
        self._logger.critical(*args, **kwargs)


    def _parse_api_response(self, method_name_int, body):
        # FIXME: The ccu is performing wrong encoding at least for output of
        # executed rega scripts. But maybe this is a generic problem. Let's see
        # and only fix the known issues for the moment.
        if method_name_int in [ "rega_run_script", "interface_get_paramset_description" ]:
            body = body.replace("\\{", "{").replace("\\[", "[")

        try:
            msg = json.loads(body)
        except Exception as e:
            raise PMException("Failed to parse response to %s (%s):\n%s\n" %
                                                    (method_name_int, e, body))

        if msg["error"] != None:
            if msg["error"]["code"] == 501 and not self.call('rega_is_present'):
                raise PMConnectionError("The logic layer (ReGa) is not available (yet). When "
                                  "the CCU has just been started, please wait some time "
                                  "and retry.")
            else:
                raise PMException("[%s] %s: %s (%s)" % (method_name_int,
                                                        msg["error"]["name"],
                                                        msg["error"]["message"],
                                                        msg["error"]["code"]))

        return msg["result"]


    def __del__(self):
        """When object is removed, the close() method is called."""
        self.close()


    def __getattr__(self, func_name):
        """Realizes dynamic methods based on the methods supported by the API.

        The method names are nearly the same as provided by the CCU
        (see http://[CCU_ADDRESS]/api/homematic.cgi or API.print_methods()).
        The method names are slighly renamed. For example CCU.getSerial() is
        available as API.ccu_get_serial() in pmatic. The translation is made
        by the _to_internal_name() method. For details take a look at that
        function.
        """
        method = self._methods.get(func_name)
        if method:
            return lambda **kwargs: self.call(func_name, **kwargs)
        else:
            raise AttributeError()


    def _to_internal_name(self, method_name_api):
        """Translates a raw API method name to the pmatic notation.

        These modifications are made:

        * . are replaced with _
        * BidCoS is replaced with bidcos
        * ReGa is replaced with rega
        * whole string is transformed from camel case to lowercase + underscore notation

        e.g. Interface.activateLinkParamset is changed to API.interface_activate_link_paramset
        """
        return utils.decamel(method_name_api.replace(".", "_").replace("BidCoS", "bidcos").replace("ReGa", "rega"))


    def _get_methods_config(self):
        """Gathers the method configuration file from the CCU.

        Returns the method configuration as list of lines. Each
        of these lines is a unicode string.

        Has to be implemented by the specific API class."""
        raise Exception("missing implementation")


    def call(self, method_name, **kwargs):
        """Realizes the API calls.

        Has to be implemented by the specific API class."""
        raise Exception("missing implementation")


    def close(self):
        """Teardown methods after use of pmatic.

        Has to be implemented by the specific API class."""
        raise Exception("missing implementation")


    def print_methods(self):
        """Prints a description of the available API methods.

        This information has been fetched from the CCU before. This might be useful
        for working with the API to gather infos about the available calls.
        """
        line_format = "%-60s %s\n"
        sys.stdout.write(line_format % ("Method", "Description"))

        # Output device API methods
        for method_name_int, method in sorted(self._methods.items()):
            call_txt = "API.%s(%s)" % (method_name_int, ", ".join(method["INT_ARGUMENTS"]))
            sys.stdout.write(line_format % (call_txt, method["INFO"]))


    def _init_methods(self):
        """Parses the method configuration read from the CCU.

        The method configuration read with _get_methods_config() is being
        parsed here to initialize the self._methods dictionary which holds
        all need information about the available API methods.
        """
        self._methods.clear()

        method_name_int = None
        for l in self._get_methods_config():
            line = l.rstrip()
            if not line:
                continue
            elif line[0] not in [ " ", "\t" ] and line[-1] == "{":
                real_method_name = line.split(" ", 1)[0]
                method_name_int = self._to_internal_name(real_method_name)
                self._methods.setdefault(method_name_int, {"NAME": real_method_name})
            elif method_name_int and line == "}":
                method_name_int = False
            elif method_name_int:
                key, val = line.lstrip().split(None, 1)
                if key == "INFO":
                    val = val[1:-1] # strip off surrounding braces

                elif key == "ARGUMENTS":
                    val = val[1:-1].split() # strip off surrounding braces, split by spaces

                    # Internal arguments have the _session_id_ removed
                    self._methods[method_name_int]["INT_ARGUMENTS"] = [ a for a in val if a != "_session_id_" ]

                self._methods[method_name_int][key] = val


    def _get_method(self, method_name_int):
        """Returns the method specification (dict) of the given API methods.

        The method name needs to be specified with it's internal name (like
        the methods of the API object are named). When the request API method
        does not exist a PMException is raised.
        """
        try:
            return self._methods[method_name_int]
        except KeyError:
            raise PMException("Method \"%s\" is not a valid method." % method_name_int)
