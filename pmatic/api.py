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

"""Provides the API interface to the CCU

This module provides you with the low level API of pmatic to the CCU.
Low level API means that it cares about connecting to the interfaces on
the CCU, authenticates with it and accesses the API calls and makes them
all available in the Python code. So that you can simply call methods on
the API object to make API calls and get Python data structures back.

The most important function of this module is the init() function. This
is the function you should call in your program code to initialize the
API object. It detects whether or not the code is run on the CCU or
a remote connection from another system is made to the CCU.
"""

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import json
import atexit

# Specific for the LocalAPI()
import subprocess

# Specific for the RemoteAPI()
try:
    from urllib.request import urlopen
    from urllib.error import URLError
    from http.client import BadStatusLine
except ImportError:
    from urllib2 import urlopen
    from urllib2 import URLError
    from httplib import BadStatusLine

try:
    # Is recommended for Python 3.x but fails on 2.7, but is not mandatory
    from builtins import object
except ImportError:
    pass

from . import PMException, PMConnectionError, init_logger, utils


def init(mode=None, **kwargs):
    """Wrapper to create the API object you need to acces the CCU API.

    By default it detects whether or not this code is being executed on the CCU
    or on another system. And initializes either a LocalAPI() object when run
    directly on a CCU or, in all other cases, a RemoteAPI() object. This object
    is then being returned.

    You can provide the mode argument to disable auto detection and either set
    it to "local" to enforce a LocalAPI() object to be created or "remote" to
    enforce a RemoteAPI() object.

    In case a RemoteAPI() object is being created, you need to provide at least
    the additional keyword arguments address="http://[HOST]" which needs to
    contain the base URL to your CCU together with credentials=("[USER]", "PASSWORD")
    which must be valid credentials to authenticate with the CCU.
    """
    if mode == None:
        mode = is_ccu() and "local" or "remote"

    if mode == "local":
        if not is_ccu():
            raise PMException("local mode can only be used on the CCU.")

        return LocalAPI(**kwargs)
    elif mode == "remote":
        try:
            return RemoteAPI(**kwargs)
        except TypeError as e:
            raise PMException("You need to provide at least the address and credentials "
                              "to access your CCU (%s)." % e)
    else:
        raise PMException("Invalid mode given. Valid ones are \"local\" and \"remote\".")


def is_ccu():
    """Returns True when executed on a CCU device. Otherwise False is being returned."""
    return "ccu" in os.uname()



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



class RemoteAPI(AbstractAPI):
    """Provides API access via HTTP to the CCU."""
    _session_id = None

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
        self._register_atexit_handler()


    def _set_address(self, address):
        if not utils.is_string(address):
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
        elif not utils.is_string(credentials[0]):
            raise PMException("The username is of unhandled type.")
        elif not utils.is_string(credentials[1]):
            raise PMException("The username is of unhandled type.")

        self._credentials = credentials


    def _set_connect_timeout(self, timeout):
        if type(timeout) not in [ int, float ]:
            raise PMException("Invalid timeout value. Must be of type int or float.")
        self._connect_timeout = timeout


    def _get_methods_config(self):
        # Can not use API.rega_run_script() here since the method infos are not yet
        # available. User code should use API.rega_run_script().
        response = self.call("rega_run_script",
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

        response = self.call("session_login", username=self._credentials[0],
                                              password=self._credentials[1])
        if response == None:
            raise PMException("Login failed: Got no session id.")
        self._session_id = response


    def logout(self):
        if self._session_id:
            self.call("session_logout", _session_id_=self._session_id)
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
    def _get_method(self, method_name_int):
        try:
            return super(RemoteAPI, self)._get_method(method_name_int)
        except PMException:
            if method_name_int == "session_login" and not self._methods:
                return {
                    "NAME": "Session.login",
                    "INFO": "Führt die Benutzeranmeldung durch",
                    "ARGUMENTS": [ "username", "password" ],
                }
            elif method_name_int == "rega_is_present" and not self._methods:
                return {
                    "NAME": "ReGa.isPresent",
                    "INFO": "Prüft, ob die Logikschicht (ReGa) aktiv ist",
                    "ARGUMENTS": [ ],
                }
            elif method_name_int == "rega_run_script" and not self._methods:
                return {
                    "NAME": "ReGa.runScript",
                    "INFO": "Führt ein HomeMatic Script aus",
                    "ARGUMENTS": [ "_session_id_", "script" ],
                }
            elif method_name_int == "session_logout" and not self._methods:
                return {
                    "NAME": "Session.logout",
                    "INFO": "Beendet eine Sitzung",
                    "ARGUMENTS": [ "_session_id_" ],
                }
            else:
                raise


    # Runs the provided method, which needs to be one of the methods which are available
    # on the device (with the given arguments) on the CCU.
    def call(self, method_name_int, **kwargs):
        method = self._get_method(method_name_int)
        args   = self.get_arguments(method, kwargs)

        self.debug("CALL: %s ARGS: %r" % (method["NAME"], args))

        json_data = json.dumps({
            "method": method["NAME"],
            "params": args,
        })
        url = "%s/api/homematic.cgi" % self._address

        try:
            self.debug("  URL: %s DATA: %s" % (url, json_data))
            handle = urlopen(url, data=json_data.encode("utf-8"),
                             timeout=self._connect_timeout)
        except Exception as e:
            if type(e) == URLError:
                msg = e.reason
            elif type(e) == BadStatusLine:
                msg = "Request terminated. Is the device rebooting?"
            else:
                msg = e
            raise PMConnectionError("Unable to open \"%s\" [%s]: %s" % (url, type(e).__name__, msg))

        response_txt = ""
        for line in handle.readlines():
            response_txt += line.decode("utf-8")

        http_status = handle.getcode()

        self.debug("  HTTP-STATUS: %d" % http_status)
        if http_status != 200:
            raise PMException("Error %d opening \"%s\" occured: %s" %
                                    (http_status, url, response_txt))

        self.debug("  RESPONSE: %s" % response_txt)
        return self._parse_api_response(method_name_int, response_txt)


    @property
    def address(self):
        return self._address



class LocalAPI(AbstractAPI):
    """Realizes the pmatic API when executed on locally on the CCU."""
    _methods_file = "/www/api/methods.conf"

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
            "array set METHOD_LIST  [file_load %s]\n" % self._methods_file
        )


    def _get_methods_config(self):
        return open(self._methods_file).read().decode("latin-1").split("\r\n")


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
        """Closes the "connection" with the CCU. In fact it terminates the tclsh process."""
        if self._tclsh:
            self._tclsh.kill()
