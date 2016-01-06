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

import subprocess

from .. import PMException
from .abstract import AbstractAPI

class LocalAPI(AbstractAPI):
    methods_file = "/www/api/methods.conf"

    def __init__(self, **kwargs):
        self._tclsh   = None

        super(LocalAPI, self).__init__(kwargs.get("logger"),
                                       kwargs.get("log_level"))

        self._init_tclsh()
        self._init_methods()
        self._register_atexit_handler()


    def _init_tclsh(self):
        try:
            self._tclsh = subprocess.Popen(["/bin/tclsh"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, #stderr=subprocess.PIPE,
                cwd="/www/api",
                shell=False)
        except OSError as e:
            if e.errno == 2:
                raise PMException("Could not find /bin/tclsh. Maybe running local API on non CCU device?")
            else:
                raise

        self._tclsh.stdin.write(
            "load tclrega.so\n"
            "source /www/api/eq3/common.tcl\n"
            "source /www/api/eq3/ipc.tcl\n"
            "source /www/api/eq3/json.tcl\n"
            "source /www/api/eq3/jsonrpc.tcl\n"
            "source /www/api/eq3/hmscript.tcl\n"
            "source /www/api/eq3/event.tcl\n"
            "array set INTERFACE_LIST [ipc_getInterfaces]\n"
            "array set METHOD_LIST  [file_load %s]\n" % self.methods_file
        )


    def _get_methods_config(self):
        return open(self.methods_file).read().decode("latin-1").split("\r\n")


    def _get_args(self, method, args):
        if not args:
            return "[]"

        args_parsed = "[list "
        for arg_name in method["ARGUMENTS"]:
            try:
                if arg_name == "_session_id_" and arg_name not in args:
                    val = "\"\"" # Fake default session id. Not needed for local API
                else:
                    val = args[arg_name]
                    if val == None:
                        val = "\"\""

                args_parsed += arg_name + " " + val + " "
            except KeyError:
                raise PMException("Missing argument \"%s\". Needs: %s" %
                                (arg_name, ", ".join(method["ARGUMENTS"])))
        return args_parsed.rstrip(" ") + "]"


    def call(self, method_name_int, **kwargs):
        """Runs the given API method directly on the CCU using a tclsh process

        The API method needs to be one of the methods which are available
        on the device (with the given arguments)."""
        method = self._get_method(method_name_int)
        parsed_args = self._get_args(method, kwargs)
        file_path = "/www/api/methods/%s" % method["SCRIPT_FILE"]

        self.debug("CALL: %s ARGS: %r" % (method["SCRIPT_FILE"], parsed_args))

        tcl = ""

        # \0\n is written to stdout of the tclsh process to mark and detect the
        # end of the output of the API call.
        tcl += \
            "array set method $METHOD_LIST(%s)\n" \
            "array set args %s\n" \
            "source %s\n" \
            "puts \0\n" % (method["NAME"], parsed_args, file_path)

        self.debug("  TCL: %r" % (tcl))

        self._tclsh.stdin.write(tcl)

        response_txt = ""
        while True:
            line = self._tclsh.stdout.readline().decode("latin-1")
            if not line or (len(line) > 1 and line[-2] == "\0"):
                response_txt += line[:-2] + "\n"
                break # found our terminator (see above)
            else:
                response_txt += line

        self.debug("  RESPONSE: %r" % response_txt)
        header, body = response_txt.split("\n\n", 1)

        return self._parse_api_response(method_name_int, body)


    def close(self):
        if self._tclsh:
            self._tclsh.kill()



# Old local approach: Call the homematic.cgi locally. The drawbacks:
# - needs authentication and authorization
# - little more complex (maybe a bit less performat)
#
#def post(data):
#    env = {
#        "DOCUMENT_ROOT"  : "/www/",
#        "REQUEST_METHOD" : "POST",
#    }
#
#    json_data = json.dumps(data)
#    env["CONTENT_LENGTH"] = str(len(json_data))
#
#    p = subprocess.Popen("/www/api/homematic.cgi", stdin=subprocess.PIPE,
#                         stdout=subprocess.PIPE,
#                         env=env, cwd="/www/api")
#
#    response_txt = ""
#    p.stdin.write(json_data)
#    for line in p.stdout:
#        response_txt += line
#
#    return parse_api_response(response_txt)
