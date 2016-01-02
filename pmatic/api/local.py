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

import subprocess

from .. import PMException
from .abstract import AbstractAPI

class LocalAPI(AbstractAPI):
    def __init__(self, logger=None, log_level=None):
        self._tclsh   = None

        super(LocalAPI, self).__init__(logger, log_level)

        self._init_tclsh()
        self._init_methods()


    def _init_tclsh(self):
        try:
            self._tclsh = subprocess.Popen(["/bin/tclsh"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, #stderr=subprocess.PIPE,
                cwd="/",
                shell=False)
        except OSError, e:
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
        )


    def _get_methods_config(self):
        methods_file = "/www/api/methods.conf"
        return file(methods_file).readlines()


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


    # Runs the provided method, which needs to be one of the methods which are available
    # on the device (with the given arguments) on the CCU.
    def call(self, method_name, **kwargs):
        method = self._get_method(method_name)
        parsed_args = self._get_args(method, kwargs)
        file_path = "/www/api/methods/%s" % method["SCRIPT_FILE"]

        tcl = \
            "array set args %s\n" \
            "source %s\n" \
            "puts \0\n" % (parsed_args, file_path)
        self._tclsh.stdin.write(tcl)

        response_txt = ""
        while True:
            c = self._tclsh.stdout.read(1)
            if c == "\0":
                break
            else:
                response_txt += c
        header, body = response_txt.split("\n\n", 1)

        return self._parse_api_response(body)


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
