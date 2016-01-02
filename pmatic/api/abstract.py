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

import json, sys
from .. import PMException, init_logger

class AbstractAPI(object):
    def __init__(self, logger, log_level):
        self._methods = {}
        self._init_logger(logger, log_level)


    def _init_logger(self, logger, log_level):
        if logger == None:
            self._logger = init_logger(log_level)
        else:
            self._logger = logger


    def logger(self):
        return self._logger


    def debug(self, *args, **kwargs):
        self._logger.debug(*args, **kwargs)


    def info(self, *args, **kwargs):
        self._logger.info(*args, **kwargs)


    def warning(self, *args, **kwargs):
        self._logger.warning(*args, **kwargs)


    def error(self, *args, **kwargs):
        self._logger.error(*args, **kwargs)


    def critical(self, *args, **kwargs):
        self._logger.critical(*args, **kwargs)


    def _parse_api_response(self, method, body):
        # FIXME: The ccu is performing wrong encoding at least for output of
        # executed rega scripts. But maybe this is a generic problem. Let's see
        # and only fix the known issues for the moment.
        if method == "ReGa.runScript":
            body = body.replace("\\{", "{").replace("\\[", "[")

        try:
            msg = json.loads(body)
        except Exception:
            raise PMException("Failed to parse response:\n%s\n" % body)

        if msg["error"] != None:
            # FIXME: msg["error"]["code"] == 501 can also be provided during
            # restart of the CCU while ReGa is not running. Check this using
            # e.g. http://ccu/ise/checkrega.cgi and provide a nicer error msg.
            raise PMException("[%s] %s: %s (%s)" % (method, msg["error"]["name"],
                                                    msg["error"]["message"],
                                                    msg["error"]["code"]))

        return msg["result"]


    def __del__(self):
        self.close()


    # Realizes dynamic methods based on the methods supported by the API.
    # The method names are nearly the same for the LocalAPI
    # (except the dots). e.g.
    # -> CCU.getSerial() is available as API.CCU_getSerial()
    def __getattr__(self, func_name):
        method = self._methods.get(func_name)
        if method:
            return lambda **kwargs: self.call(func_name, **kwargs)
        else:
            raise AttributeError()


    def _to_internal_name(self, method_name):
        return method_name.replace(".", "_")


    def _get_methods_config(self):
        raise Exception("missing implementation")


    def call(self, method_name, **kwargs):
        raise Exception("missing implementation")


    def close(self):
        raise Exception("missing implementation")


    # Prints a description of the available API methods. This information
    # has been fetched from the CCU before. This might be useful for working
    # with the API to gather infos about the available calls.
    def print_methods(self):
        line_format = "%-60s %s\n"
        sys.stdout.write(line_format % ("Method", "Description"))

        # Output device API methods
        for method_name_int, method in sorted(self._methods.items()):
            call_txt = "API.%s(%s)" % (method_name_int, ", ".join(method["INT_ARGUMENTS"]))
            sys.stdout.write(line_format % (call_txt, method["INFO"]))


    def _init_methods(self):
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
                    # FIXME: Decode to unicode string
                    val = val[1:-1] # strip off surrounding braces

                elif key == "ARGUMENTS":
                    val = val[1:-1].split() # strip off surrounding braces, split by spaces

                    # Internal arguments have the _session_id_ removed
                    self._methods[method_name_int]["INT_ARGUMENTS"] = [ a for a in val if a != "_session_id_" ]

                self._methods[method_name_int][key] = val


    def _get_method(self, method_name):
        try:
            return self._methods[self._to_internal_name(method_name)]
        except KeyError:
            raise PMException("Method \"%s\" is not a valid method." % method_name)
