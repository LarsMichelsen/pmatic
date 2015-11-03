#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - A simple API to to the Homematic CCU2
# Copyright (C) 2015 Lars Michelsen <lm@larsmichelsen.com>
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

import urllib2, json
from .. import PMException
from .abstract import API

class RemoteAPI(API):
    def __init__(self, address, credentials, connect_timeout=10, logger=None, log_level=None):
        self._session_id      = None
        self._address         = None
        self._credentials     = None
        self._connect_timeout = None

        super(RemoteAPI, self).__init__(logger, log_level)

        self._set_address(address)
        self._set_credentials(credentials)
        self._set_connect_timeout(connect_timeout)

        self.login()
        self._init_methods()


    def _set_address(self, address):
        if type(address) not in [ str, unicode ]:
            raise PMException("Please specify the address of the CCU.")

        # Add optional protocol prefix
        if not address.startswith("https://") and not address.startswith("http://"):
            address = "http://%s" % address

        self._address = address


    def _set_credentials(self, credentials):
        if type(credentials) != tuple:
            raise PMException("Please specify the user credentials to log in to the CCU like this: \"(username, password)\".")
        elif len(credentials) != 2:
            raise PMException("The credentials must be given as tuple of two elements.")
        elif type(credentials[0]) not in [ str, unicode ]:
            raise PMException("The username is of unhandled type.")
        elif type(credentials[1]) not in [ str, unicode ]:
            raise PMException("The username is of unhandled type.")

        self._credentials = credentials


    def _set_connect_timeout(self, timeout):
        if type(timeout) not in [ int, float ]:
            raise PMException("Invalid timeout value. Must be of type int or float.")
        self._connect_timeout = timeout


    def _get_methods_config(self):
        # Can not use API.ReGa_runScript() here since the method infos are not yet
        # available. User code should use API.ReGa_runScript().
        response = self.call("ReGa.runScript",
            _session_id_=self._session_id,
            script="string stderr;\n"
                   "string stdout;\n"
                   "system.Exec(\"cat /www/api/methods.conf\", &stdout, &stderr);\n"
                   "Write(stdout);\n"
        )
        return response.split("\r\n")


    def login(self):
        if self._session_id:
            raise PMException("Already logged in.")

        response = self.call("Session.login", username=self._credentials[0],
                                              password=self._credentials[1])
        if response == None:
            raise PMException("Login failed: Got no session id.")
        self._session_id = response


    def logout(self):
        if self._session_id:
            self.call("Session.logout", _session_id_=self._session_id)
            self._session_id = None


    def close(self):
        self.logout()


    def get_arguments(self, method, args):
        if "_session_id_" in method["ARGUMENTS"] and self._session_id:
            args["_session_id_"] = self._session_id
        return args


    # The following wrapper allows specific API calls which are needed
    # before the real list of methods is available, so allow
    # it to be not validated and fake the method response.
    def _get_method(self, method_name):
        try:
            return super(RemoteAPI, self)._get_method(method_name)
        except PMException:
            if method_name == "Session.login" and not self._methods:
                return {
                    "NAME": "Session.login",
                    "INFO": "Führt die Benutzeranmeldung durch",
                    "ARGUMENTS": [ "username", "password" ],
                }
            elif method_name == "ReGa.runScript" and not self._methods:
                return {
                    "NAME": "ReGa.runScript",
                    "INFO": "Führt ein HomeMatic Script aus",
                    "ARGUMENTS": [ "_session_id_", "script" ],
                }
            elif method_name == "Session.logout" and not self._methods:
                return {
                    "NAME": "Session.logout",
                    "INFO": "Beendet eine Sitzung",
                    "ARGUMENTS": [ "_session_id_" ],
                }
            else:
                raise


    # Runs the provided method, which needs to be one of the methods which are available
    # on the device (with the given arguments) on the CCU.
    def call(self, method_name, **kwargs):
        method = self._get_method(method_name)
        args   = self.get_arguments(method, kwargs)

        self.debug("CALL: %s ARGS: %r" % (method["NAME"], args))

        json_data = json.dumps({
            "method": method["NAME"],
            "params": args,
        })
        url = "%s/api/homematic.cgi" % self._address
        try:
            self.debug("  URL: %s DATA: %s" % (url, json_data))
            handle = urllib2.urlopen(url, data=json_data, timeout=self._connect_timeout)
        except urllib2.URLError, e:
            raise PMException("Failed to open \"%s\": %s" % (url, e.reason))
        except Exception, e:
            raise PMException("Failed to open \"%s\": %s" % (url, e))

        response_txt = ""
        for line in handle.readlines():
            response_txt += line

        http_status = handle.getcode()

        self.debug("  HTTP-STATUS: %d" % http_status)
        if http_status != 200:
            raise PMException("Error %d opening \"%s\" occured: %s" %
                                    (http_status, url, response_txt))

        self.debug("  RESPONSE: %s" % response_txt)
        return self._parse_api_response(method_name, response_txt)
