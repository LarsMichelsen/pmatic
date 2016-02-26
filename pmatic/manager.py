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

"""Implements the main components of the pmatic manager"""

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:
    # Is recommended for Python 3.x but fails on 2.7, but is not mandatory
    from builtins import object
except ImportError:
    pass

import os
import cgi
import sys
import time
import json
import socket
import signal
import inspect
import traceback
import threading
import subprocess
from wsgiref.handlers import SimpleHandler
import wsgiref.simple_server
from Cookie import SimpleCookie
from hashlib import sha256
from grp import getgrnam
from pwd import getpwnam

import pmatic
import pmatic.utils as utils
from pmatic.exceptions import PMUserError, SignalReceived

# Set while a script is executed with the "/run" page
g_runner = None

class Config(utils.LogMixin):
    config_path = "/etc/config/addons/pmatic/etc"
    script_path = "/etc/config/addons/pmatic/scripts"
    static_path = "/etc/config/addons/pmatic/manager_static"

    ccu_enabled     = True
    ccu_address     = None
    ccu_credentials = None

    log_level = None
    log_file  = "/var/log/pmatic-manager.log"

    pushover_api_token = None
    pushover_user_token = None

    @classmethod
    def load(cls):
        try:
            try:
                fh = open(cls.config_path + "/manager.config")
                config = json.load(fh)
            except IOError as e:
                # a non existing file is allowed.
                if e.errno == 2:
                    config = {}
                else:
                    raise
        except Exception as e:
            cls.cls_logger().error("Failed to load config: %s. Terminating." % e)
            sys.exit(1)

        for key, val in config.items():
            setattr(cls, key, val)


    @classmethod
    def save(cls):
        config = {}

        for key, val in cls.__dict__.items():
            if key[0] != "_" and key not in [ "config_path", "script_path",
                                              "static_path", "log_file" ] \
               and not inspect.isroutine(val):
                config[key] = val

        json_config = json.dumps(config)
        open(cls.config_path + "/manager.config", "w").write(json_config + "\n")



# FIXME This handling is only for testing purposes and will be cleaned up soon
if not utils.is_ccu():
    Config.script_path = "/tmp/pmatic-scripts"
    Config.static_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) \
                         + "/manager_static"
    Config.config_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) \
                         + "/etc"
    Config.ccu_address = "http://192.168.1.26"
    Config.ccu_credentials = ("Admin", "EPIC-SECRET-PW")



class Html(object):
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
    }

    def page_header(self):
        self.write('<!DOCTYPE HTML>\n'
                   '<html><head>\n')
        self.write("<meta http-equiv=\"Content-Type\" "
                   "content=\"text/html; charset=utf-8\">\n")
        self.write("<meta http-equiv=\"X-UA-Compatible\" "
                   "content=\"IE=edge\">\n")
        self.write("<link rel=\"stylesheet\" href=\"css/font-awesome.min.css\">\n")
        self.write("<link rel=\"stylesheet\" href=\"css/pmatic.css\">\n")
        self.write("<link rel=\"shortcut icon\" href=\"favicon.ico\" type=\"image/ico\">\n")
        self.write('<title>%s</title>\n' % self.title())
        self.write('</head>\n')
        self.write("<body>\n")


    def page_footer(self):
        self.write("</body>")
        self.write("</html>")


    def navigation(self):
        self.write("<ul id=\"navigation\">\n")
        self.write("<li><a href=\"/\"><i class=\"fa fa-code\"></i>Scripts</a></li>\n")
        self.write("<li><a href=\"/run\"><i class=\"fa fa-flash\"></i>Execute Scripts</a></li>\n")
        self.write("<li><a href=\"/event_log\"><i class=\"fa fa-list\"></i>Event Log</a></li>\n")
        self.write("<li><a href=\"/config\"><i class=\"fa fa-gear\"></i>Configuration</a></li>\n")
        self.write("<li class=\"right\"><a href=\"https://larsmichelsen.github.io/pmatic/\" "
                   "target=\"_blank\">pmatic %s</a></li>\n" % pmatic.__version__)
        self.write("</ul>\n")


    def is_action(self):
        return bool(self._vars.getvalue("action"))


    def begin_form(self, multipart=None):
        enctype = " enctype=\"multipart/form-data\"" if multipart else ""
        target_url = self.url or "/"
        self.write("<form method=\"post\" action=\"%s\" %s>\n" % (target_url, enctype))


    def end_form(self):
        self.write("</form>\n")


    def file_upload(self, name, accept="text/*"):
        self.write("<input name=\"%s\" type=\"file\" accept=\"%s\">" %
                        (name, accept))


    def hidden(self, name, value):
        self.write("<input type=\"hidden\" name=\"%s\" value=\"%s\">\n" % (name, value))


    def password(self, name):
        self.write("<input type=\"password\" name=\"%s\">\n" % name)


    def submit(self, label, value="1"):
        self.write("<button type=\"submit\" name=\"action\" "
                   "value=\"%s\">%s</button>\n" % (value, label))


    def input(self, name, deflt=None):
        value = deflt if deflt != None else ""
        self.write("<input type=\"text\" name=\"%s\" value=\"%s\">\n" % (name, value))


    def select(self, name, choices, deflt=None):
        self.write("<select name=\"%s\">\n" % name)
        self.write("<option value=\"\"></option>\n")
        for choice in choices:
            if deflt == choice[0]:
                selected = " selected"
            else:
                selected = ""
            self.write("<option value=\"%s\"%s>%s</option>\n" % (choice[0], selected, choice[1]))
        self.write("</select>\n")


    def icon(self, icon_name, title, cls=None):
        css = " " + cls if cls else ""
        self.write("<i class=\"fa fa-%s%s\" title=\"%s\"></i>" %
                            (icon_name, css, self.escape(title)))


    def icon_button(self, icon_name, url, title):
        self.write("<a class=\"btn\" href=\"%s\">" % url)
        self.icon(icon_name, title)
        self.write("</a>")


    def error(self, text):
        self.message(text, "error", "bomb")


    def success(self, text):
        self.message(text, "success", "check-circle-o")


    def info(self, text):
        self.message(text, "info", "info-circle")


    def message(self, text, cls, icon):
        self.write("<div class=\"message %s\"><i class=\"fa fa-2x fa-%s\"></i> "
                   "%s</div>\n" % (cls, icon, text))


    def h2(self, title):
        self.write("<h2>%s</h2>\n" % self.escape(title))


    def h3(self, title):
        self.write("<h3>%s</h3>\n" % self.escape(title))


    def p(self, content):
        self.write("<p>%s</p>\n" % content)


    def js_file(self, url):
        self.write("<script type=\"text/javascript\" src=\"%s\"></script>\n" % url)


    def js(self, script):
        self.write("<script type=\"text/javascript\">%s</script>\n" % script)


    def redirect(self, delay, url):
        self.js("setTimeout(\"location.href = '%s';\", %d);" % (url, delay*1000))


    def escape(self, text):
        """Escape text for embedding into HTML code."""
        return "".join(self.html_escape_table.get(c, c) for c in text)


    def write_text(self, text):
        self.write(self.escape(text))


class FieldStorage(cgi.FieldStorage):
    def getvalue(self, key, default=None):
        value = cgi.FieldStorage.getvalue(self, key.encode("utf-8"), default)
        if value is not None:
            return value.decode("utf-8")
        else:
            return None



class PageHandler(object):
    @classmethod
    def pages(cls):
        pages = {}
        for subclass in cls.__subclasses__():
            if hasattr(subclass, "url"):
                pages[subclass.url] = subclass
        return pages


    @classmethod
    def base_url(self, environ):
        parts = environ['PATH_INFO'][1:].split("/")
        return parts[0]


    @classmethod
    def get(cls, environ):
        pages = cls.pages()
        try:
            page = pages[cls.base_url(environ)]

            if cls.is_password_set() and not cls._is_authenticated(environ):
                return pages["login"]
            else:
                return page
        except KeyError:
            static_file_class = StaticFile.get(environ['PATH_INFO'])
            if not static_file_class:
                return pages["404"]
            else:
                return static_file_class


    @classmethod
    def is_password_set(self):
        return os.path.exists(os.path.join(Config.config_path, "manager.secret"))


    @classmethod
    def _get_auth_cookie_value(self, environ):
        for name, cookie in SimpleCookie(environ.get("HTTP_COOKIE")).items():
            if name == "pmatic_auth":
                return cookie.value


    @classmethod
    def _is_authenticated(self, environ):
        value = self._get_auth_cookie_value(environ)
        if not value or value.count(":") != 1:
            return False

        salt, salted_hash = value.split(":", 1)

        filepath = os.path.join(Config.config_path, "manager.secret")
        secret = open(filepath).read().strip()

        correct_hash = sha256(secret + salt).hexdigest().decode("utf-8")

        return salted_hash == correct_hash


    def __init__(self, manager, environ, start_response):
        self._manager = manager
        self._env = environ
        self._start_response = start_response

        self._http_headers = [
            (b'Content-type', self._get_content_type().encode("utf-8")),
        ]
        self._page = []

        self._read_environment()


    def _get_content_type(self):
        return b'text/html; charset=UTF-8'


    def _read_environment(self):
        self._read_vars()


    def _set_cookie(self, name, value):
        cookie = SimpleCookie()
        cookie[name.encode("utf-8")] = value.encode("utf-8")
        self._http_headers.append((b"Set-Cookie", cookie[name.encode("utf-8")].OutputString()))


    def _read_vars(self):
        wsgi_input = self._env["wsgi.input"]
        if not wsgi_input:
            self._vars = cgi.FieldStorage()
            return

        self._vars = FieldStorage(fp=wsgi_input, environ=self._env,
                                  keep_blank_values=1)


    def _send_http_header(self):
        self._start_response(self._http_status(200), self._http_headers)


    def process_page(self):
        self._send_http_header()

        self.page_header()
        self.navigation()
        self.write("<div id=\"content\">\n")

        if self.is_action():
            try:
                self.action()
            except PMUserError as e:
                self.error(e)
            except Exception as e:
                self.error("Unhandled exception: %s" % e)

        try:
            self.process()
        except PMUserError as e:
            self.error(e)
        except Exception as e:
            self.error("Unhandled exception: %s" % e)

        self.write("\n</div>")
        self.page_footer()

        return self._page


    def ensure_password_is_set(self):
        if not self.is_password_set():
            raise PMUserError("To be able to access this page you first have to "
                            "<a href=\"/config\">set a password</a> and authenticate "
                            "afterwards.")


    def title(self):
        return "No title specified"


    def action(self):
        self.write("Not implemented yet.")


    def process(self):
        self.write("Not implemented yet.")


    def write(self, code):
        if utils.is_text(code):
            code = code.encode("utf-8")
        self._page.append(code)


    def _http_status(self, code):
        if code == 200:
            return b'200 OK'
        elif code == 301:
            return b'301 Moved Permanently'
        elif code == 302:
            return b'302 Found'
        elif code == 304:
            return b'304 Not Modified'
        elif code == 404:
            return b'404 Not Found'
        elif code == 500:
            return b'500 Internal Server Error'
        else:
            return str(code)



class StaticFile(PageHandler):
    @classmethod
    def get(self, path_info):
        if ".." in path_info:
            return # don't allow .. in paths to prevent opening of unintended files

        if path_info.startswith("/css/") or path_info.startswith("/fonts/") \
           or path_info.startswith("/scripts/") or path_info.startswith("/js/"):
            file_path = StaticFile.system_path_from_pathinfo(path_info)
            if os.path.exists(file_path):
                return StaticFile


    @classmethod
    def system_path_from_pathinfo(self, path_info):
        if path_info.startswith("/scripts/"):
            return os.path.join(Config.script_path, path_info[9:])
        else:
            return os.path.join(Config.static_path, path_info.lstrip("/"))


    def _get_content_type(self):
        ext = self._env["PATH_INFO"].split(".")[-1]
        if ext == "css":
            return "text/css; charset=UTF-8"
        if ext == "js":
            return "application/x-javascript; charset=UTF-8"
        elif ext == "otf":
            return "application/vnd.ms-opentype"
        elif ext == "eot":
            return "application/vnd.ms-fontobject"
        elif ext == "ttf":
            return "application/x-font-ttf"
        elif ext == "woff":
            return "application/octet-stream"
        elif ext == "woff2":
            return "application/octet-stream"
        else:
            return "text/plain; charset=UTF-8"


    def _check_cached(self, file_path):
        client_cached_age = self._env.get('HTTP_IF_MODIFIED_SINCE', None)
        if not client_cached_age:
            return False

        # Try to parse the If-Modified-Since HTTP header provided by
        # the client to make client cache usage possible.
        try:
            t = time.strptime(client_cached_age, "%a, %d %b %Y %H:%M:%S %Z")
            if t == time.gmtime(os.stat(file_path).st_mtime):
                return True
        except ValueError:
            # strptime raises ValueError when wrong time format is being provided
            return False


    def process_page(self):
        path_info = self._env["PATH_INFO"]
        file_path = StaticFile.system_path_from_pathinfo(self._env["PATH_INFO"])

        is_cached = self._check_cached(file_path)
        if is_cached:
            self._start_response(self._http_status(304), [])
            return []

        mtime = os.stat(file_path).st_mtime
        self._http_headers.append((b"Last-Modified",
                    time.strftime("%a, %d %b %Y %H:%M:%S UTC", time.gmtime(mtime))))

        if path_info.startswith("/scripts"):
            self._http_headers.append((b"Content-Disposition",
                b"attachment; filename=\"%s\"" % os.path.basename(path_info)))

        self._start_response(self._http_status(200), self._http_headers)
        return [ l for l in open(file_path) ]



class AbstractScriptPage(object):
    def _get_scripts(self):
        if not os.path.exists(Config.script_path):
            raise PMUserError("The script directory %s does not exist." %
                                                    Config.script_path)

        for dirpath, dirnames, filenames in os.walk(Config.script_path):
            if dirpath == Config.script_path:
                relpath = ""
            else:
                relpath = dirpath[len(Config.script_path)+1:]

            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath) and filename[0] != ".":
                    if relpath:
                        yield os.path.join(relpath, filename)
                    else:
                        yield filename



class PageMain(PageHandler, Html, AbstractScriptPage, utils.LogMixin):
    url = ""

    def title(self):
        return "Manage pmatic Scripts"


    def save_script(self, filename, script):
        if not os.path.exists(Config.script_path):
            os.makedirs(Config.script_path)

        filepath = os.path.join(Config.script_path, filename)
        open(filepath, "w").write(script)
        os.chmod(filepath, 0o755)


    def action(self):
        self.ensure_password_is_set()
        action = self._vars.getvalue("action")
        if action == "upload":
            self._handle_upload()
        elif action == "delete":
            self._handle_delete()


    def _handle_upload(self):
        if not self._vars.getvalue("script"):
            raise PMUserError("You need to select a script to upload.")

        filename = self._vars["script"].filename
        script = self._vars["script"].file.read()
        first_line = script.split(b"\n", 1)[0]

        if not first_line.startswith(b"#!/usr/bin/python") \
           and not first_line.startswith(b"#!/usr/bin/env python"):
            raise PMUserError("The uploaded file does not seem to be a pmatic script.")

        if len(script) > 1048576:
            raise PMUserError("The uploaded file is too large.")

        self.save_script(filename, script)
        self.success("The script has been uploaded.")


    def _handle_delete(self):
        filename = self._vars.getvalue("script")

        if not filename:
            raise PMUserError("You need to provide a script name to delete.")

        if filename not in self._get_scripts():
            raise PMUserError("This script does not exist.")

        filepath = os.path.join(Config.script_path, filename)
        os.unlink(filepath)
        self.success("The script has been deleted.")


    def process(self):
        self.ensure_password_is_set()
        self.upload_form()
        self.scripts()


    def upload_form(self):
        self.h2("Upload Script")
        self.p("You can either upload your scripts using this form or "
               "copy the files on your own, e.g. using SFTP or SCP, directly "
               "to <tt>%s</tt>." % Config.script_path)
        self.p("Please note that existing scripts with equal names will be overwritten "
               "without warning.")
        self.write("<div class=\"upload_form\">\n")
        self.begin_form(multipart=True)
        self.file_upload("script")
        self.submit("Upload script", "upload")
        self.end_form()
        self.write("</div>\n")


    def scripts(self):
        self.h2("Scripts")
        self.write("<div class=\"scripts\">\n")
        self.write("<table><tr>\n")
        self.write("<th>Actions</th>"
                   "<th class=\"largest\">Filename</th>"
                   "<th>Last modified</th></tr>\n")
        for filename in self._get_scripts():
            path = os.path.join(Config.script_path, filename)
            last_mod_ts = os.stat(path).st_mtime

            self.write("<tr>")
            self.write("<td>")
            self.icon_button("trash", "?action=delete&script=%s" % filename,
                              "Delete this script")
            self.icon_button("bolt", "/run?script=%s&action=run" % filename,
                              "Execute this script now")
            self.icon_button("download", "/scripts/%s" % filename,
                              "Download this script")
            self.write("</td>")
            self.write("<td>%s</td>" % filename)
            self.write("<td>%s</td>" % time.strftime("%Y-%m-%d %H:%M:%S",
                                                     time.localtime(last_mod_ts)))
            self.write("</tr>")
        self.write("</table>\n")
        self.write("</div>\n")



class PageRun(PageHandler, Html, AbstractScriptPage, utils.LogMixin):
    url = "run"

    def title(self):
        return "Execute pmatic Scripts"


    def action(self):
        self.ensure_password_is_set()
        action = self._vars.getvalue("action")
        if action == "run":
            self._handle_run()
        elif action == "abort":
            self._handle_abort()


    def _handle_run(self):
        script = self._vars.getvalue("script")
        if not script:
            raise PMUserError("You have to select a script.")

        if script not in self._get_scripts():
            raise PMUserError("You have to select a valid script.")

        if self._is_running():
            raise PMUserError("There is another script running. Wait for it to complete "
                            "or stop it to be able to execute another script.")

        self._execute_script(script)
        self.success("The script has been started.")


    def _handle_abort(self):
        if not self._is_running():
            raise PMUserError("There is no script running to abort.")

        self._abort_script()
        self.success("The script has been aborted.")


    def process(self):
        self.ensure_password_is_set()
        self._start_form()
        self._progress()


    def _start_form(self):
        self.h2("Execute Scripts")
        self.p("This page is primarily meant for testing purposes. You can choose "
               "which script you like to execute and then start it. The whole output of "
               "the script is captured and shown in the progress area below. You "
               "can execute only one script at the time. Please note: You are totally "
               "free to execute your scripts on the command line or however you like.")
        self.write("<div class=\"execute_form\">\n")
        self.begin_form()
        self.write("Select the script: ")
        self.select("script", sorted([ (s, s) for s in self._get_scripts() ]))
        self.submit("Run script", "run")
        self.end_form()
        self.write("</div>\n")


    def _progress(self):
        self.h2("Progress")
        if not self._is_started():
            self.p("There is no script running.")
            return

        self.write("<table>")
        self.write("<tr><th>Script</th>"
                   "<td>%s</td></tr>" % g_runner.script)
        self.write("<tr><th>Started at</th>"
                   "<td>%s</td></tr>" % time.strftime("%Y-%m-%d %H:%M:%S",
                                                      time.localtime(g_runner.started)))

        self.write("<tr><th>Finished at</th>"
                   "<td>")
        if not self._is_running() and g_runner.finished != None:
            self.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(g_runner.finished)))
        else:
            self.write("-")
        self.write("</td></tr>")

        self.write("<tr><th>Current state</th>"
                   "<td>")
        if self._is_running():
            self.icon("spinner", "The script is running...", cls="fa-pulse")
            self.write(" Running... ")
            self.icon_button("close", "/run?action=abort", "Stop this script.")
        elif g_runner.exit_code != None:
            if g_runner.exit_code == 0:
                self.icon("check", "Successfully finished")
            else:
                self.icon("times", "An error occured")
            self.write(" Finished (Exit code: <tt>%d</tt>)" % g_runner.exit_code)
        else:
            self.icon("times", "Not running")
            self.write(" Started but not running - something went wrong.")
        self.write("</td></tr>")

        self.write("<tr><th class=\"toplabel\">Output</th>")
        self.write("<td>")
        output = self.escape(self._output()) or "<i>(no output)</i>"
        self.write("<pre id=\"output\">%s</pre>" % output)
        self.write("</td></tr>")
        self.write("</table>")

        if self._is_running():
            self.js_file("js/update_output.js")


    def _is_started(self):
        return g_runner != None


    def _is_running(self):
        return g_runner and g_runner.is_alive()


    def _exit_code(self):
        return g_runner.exit_code


    def _output(self):
        return "".join(g_runner.output)


    def _execute_script(self, script):
        global g_runner
        g_runner = ScriptRunner(script)
        g_runner.start()


    def _abort_script(self):
        g_runner.abort()



class PageAjaxUpdateOutput(PageHandler, Html, utils.LogMixin):
    url = "ajax_update_output"

    def _get_content_type(self):
        return b"text/plain; charset=UTF-8"

    def process_page(self):
        output = []

        self._start_response(self._http_status(200), self._http_headers)
        if not g_runner:
            return output

        # Tell js code to continue reloading or not
        if not g_runner.is_alive():
            self.write_text("0")
        else:
            self.write_text("1")

        self.write_text("".join(g_runner.output))

        return self._page



class PageLogin(PageHandler, Html, utils.LogMixin):
    url = "login"

    def title(self):
        return "Log in to pmatic Manager"


    def action(self):
        password = self._vars.getvalue("password")

        if not password:
            raise PMUserError("Invalid password.")

        filepath = os.path.join(Config.config_path, "manager.secret")
        secret = open(filepath).read().strip()

        if secret != sha256(password).hexdigest():
            raise PMUserError("Invalid password.")

        self._login(secret)
        self.success("You have been authenticated. You can now <a href=\"/\">proceed</a>.")
        self.redirect(2, "/")


    def _login(self, secret):
        salt = "%d" % int(time.time())
        salted_hash = sha256(secret + salt).hexdigest()
        cookie_value = salt + ":" + salted_hash
        self._set_cookie("pmatic_auth", cookie_value)


    def process(self):
        self.h2("Login")
        self.p("Welcome to the pmatic Manager. Please provide your manager "
               "password to log in.")
        self.write("<div class=\"login\">\n")
        self.begin_form()
        self.password("password")
        self.submit("Log in", "login")
        self.end_form()
        self.write("</div>\n")



class PageConfiguration(PageHandler, Html, utils.LogMixin):
    url = "config"

    def title(self):
        return "Configuration of pmatic Manager"


    def action(self):
        action = self._vars.getvalue("action")
        if action == "set_password":
            self._handle_set_password()
        elif action == "save_config":
            self._handle_save_config()


    def _handle_set_password(self):
        password = self._vars.getvalue("password")

        if not password:
            raise PMUserError("You need to provide a password and it must not be empty.")

        if len(password) < 6:
            raise PMUserError("The password must have a minimal length of 6 characters.")

        filepath = os.path.join(Config.config_path, "manager.secret")
        open(filepath, "w").write(sha256(password).hexdigest()+"\n")
        self.success("The password has been set. You will be redirect to the "
                     "<a href=\"/\">login</a>.")
        self.redirect(2, "/")


    # FIXME: Validations!
    def _handle_save_config(self):
        log_level_name = self._vars.getvalue("log_level")
        if not log_level_name:
            Config.log_level = None
        else:
            Config.log_level = log_level_name

        ccu_address = self._vars.getvalue("ccu_address")
        if not ccu_address:
            Config.ccu_address = None
        else:
            Config.ccu_address = ccu_address

        ccu_username = self._vars.getvalue("ccu_username").strip()
        ccu_password = self._vars.getvalue("ccu_password")
        if not ccu_username or not ccu_password:
            Config.ccu_credentials = None
        else:
            Config.ccu_credentials = ccu_username, ccu_password

        pushover_api_token = self._vars.getvalue("pushover_api_token")
        if not pushover_api_token:
            Config.pushover_api_token = None
        else:
            Config.pushover_api_token = pushover_api_token

        pushover_user_token = self._vars.getvalue("pushover_user_token")
        if not pushover_user_token:
            Config.pushover_user_token = None
        else:
            Config.pushover_user_token = pushover_user_token

        Config.save()
        self.success("The configuration has been updated.")


    def process(self):
        self.password_form()
        self.config_form()


    def password_form(self):
        self.h2("Set Manager Password")
        self.p("To make the pmatic manager fully functional, you need to "
               "configure a password for accessing the manager first. Only after "
               "setting a password functions like uploading files are enabled.")
        self.write("<div class=\"password_form\">\n")
        self.begin_form()
        self.password("password")
        self.submit("Set Password", "set_password")
        self.end_form()
        self.write("</div>\n")


    def config_form(self):
        self.h2("Configuration")
        self.write("<div class=\"config_form\">\n")
        self.begin_form()
        self.write("<table>")
        self.write("<tr><th>Log level</th>")
        self.write("<td>")
        self.select("log_level", [ (l, l) for l in pmatic.log_level_names ], Config.log_level)
        self.write("</td>")
        self.write("<td>Log entries having the configured log level (or a worse one) are logged to"
                   " the file <tt>%s</tt> by default.</td>" % Config.log_file)
        self.write("</tr>")

        self.write("</table>")

        self.h3("Connect to remote CCU")
        self.p("You can start the pmatic Manager on another device than the CCU. In this case you "
               "have to configure the address and credentials to log into the CCU. If you start "
               "the pmatic Manager on your CCU, you can leave these options empty.")

        self.write("<table>")
        self.write("<tr><th>Address</th>")
        self.write("<td>")
        self.input("ccu_address", Config.ccu_address)
        self.write("</td>")
        self.write("</tr>")
        self.write("<tr><th>Username</th>")
        self.write("<td>")
        self.input("ccu_username", Config.ccu_credentials[0])
        self.write("</td>")
        self.write("</tr>")
        self.write("<tr><th>Password</th>")
        self.write("<td>")
        self.password("ccu_password")
        self.write("</td>")
        self.write("</tr>")
        self.write("</table>")

        self.h3("Pushover Notifications")
        self.p("If you like to use pushover notifications, you need to configure your "
               "credentials here in order to make them work.")
        self.write("<table>")
        self.write("<tr><th>API Token</th>")
        self.write("<td>")
        self.input("pushover_api_token", Config.pushover_api_token)
        self.write("</td>")
        self.write("</tr>")
        self.write("<tr><th>User/Group Token</th>")
        self.write("<td>")
        self.input("pushover_user_token", Config.pushover_user_token)
        self.write("</td>")
        self.write("</tr>")
        self.write("</table>")
        self.write("<br>")
        self.submit("Save configuration", "save_config")
        self.end_form()
        self.write("</div>\n")



class PageEventLog(PageHandler, Html, utils.LogMixin):
    url = "event_log"

    def title(self):
        return "Events received from the CCU"


    def process(self):
        self.h2("Events received from the CCU")
        self.p("This page shows the last 1000 events received from the CCU. These are events "
               "which you can register your pmatic scripts on to be called once such an event "
               "is received.")

        if not self._manager._events_initialized:
            self.info("The event processing has not been initialized yet. Please come back "
                      "in one or two minutes.")
            return

        self.p("Received <i>%d</i> events in total since the pmatic manager has been started." %
                                                    self._manager.events.num_events_total)

        self.write("<table>")
        self.write("<tr><th>Time</th><th>Device</th><th>Channel</th><th>Parameter</th>"
                   "<th>Event-Type</th><th>Value</th>")
        self.write("</tr>")
        for event in reversed(self._manager.events.events):
            #"time"           : updated_param.last_updated,
            #"time_changed"   : updated_param.last_changed,
            #"param"          : updated_param,
            #"value"          : updated_param.value,
            #"formated_value" : "%s" % updated_param,
            param = event["param"]

            if event["time"] == event["time_changed"]:
                ty = "changed"
            else:
                ty = "updated"

            self.write("<tr>")
            self.write("<td>%s</td>" % time.strftime("%Y-%m-%d %H:%M:%S",
                                                     time.localtime(event["time"])))
            self.write("<td>%s</td>" % param.channel.name)
            self.write("<td>%s</td>" % param.channel.device.name)
            self.write("<td>%s</td>" % param.title)
            self.write("<td>%s</td>" % ty)
            self.write("<td>%s (Raw value: %s)</td>" %
                            (event["formated_value"], event["value"]))
            self.write("</tr>")
        self.write("</table>")


class Page404(PageHandler, Html, utils.LogMixin):
    url = "404"


    def _send_http_header(self):
        self._start_response(self._http_status(404), self._http_headers)


    def title(self):
        return "404 - Page not Found"


    def process(self):
        self.write("The requested page could not be found.")



class ScriptRunner(threading.Thread, utils.LogMixin):
    def __init__(self, script):
        threading.Thread.__init__(self)
        self.script     = script
        self.output     = []
        self.exit_code  = None
        self.started    = time.time()
        self.finished   = None


    def run(self):
        try:
            self.logger.info("Starting script: %s" % self.script)
            script_path = os.path.join(Config.script_path, self.script)

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            self._p = subprocess.Popen(["/usr/bin/env", "python", "-u", script_path], shell=False,
                                       cwd="/", env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)

            while True:
                nextline = self._p.stdout.readline().decode("utf-8")
                if nextline == "" and self._p.poll() != None:
                    break
                self.output.append(nextline)

            self.finished  = time.time()
            self.exit_code = self._p.poll()
            self.logger.info("Finished (Exit-Code: %d)." % self.exit_code)
        except Exception as e:
            self.logger.error("Failed to execute %s: %s" % (self.script, e))
            self.logger.debug(traceback.format_exc())


    def abort(self):
        self._p.terminate()
        # And wait for the termination (at least shortly)
        timer = 10
        while timer > 0 and self._p.poll() == None:
            timer -= 1
            time.sleep(0.1)



# Hook into ServerHandler to be able to catch exceptions about disconnected clients
def _server_handler_write(self, data):
    try:
        SimpleHandler.write(self, data)
    except socket.error as e:
        # Client disconnected while answering it's request.
        if e.errno != 32:
            raise


wsgiref.simple_server.ServerHandler.server_software = 'pmatic-manager'
# Found no elegant way to patch it. Sorry.
wsgiref.simple_server.ServerHandler.write = _server_handler_write


class Manager(wsgiref.simple_server.WSGIServer, utils.LogMixin):
    def __init__(self, address):
        wsgiref.simple_server.WSGIServer.__init__(
            self, address, RequestHandler)
        self.set_app(self._request_handler)

        self.ccu = None
        self._events_initialized = False

        self._init_ccu()
        self.events = Events()


    def _init_ccu(self):
        if Config.ccu_enabled:
            self.logger.info("Initializing connection with CCU")
            self.ccu = pmatic.CCU(address=Config.ccu_address,
                                  credentials=Config.ccu_credentials)
        else:
            self.logger.info("Connection with CCU is disabled")
            self.ccu = None


    def _request_handler(self, environ, start_response):
        # handler_class may be any subclass of PageHandler
        handler_class = PageHandler.get(environ)
        page = handler_class(self, environ, start_response)
        return page.process_page()


    def process_request(self, request, client_address):
        try:
            super(Manager, self).process_request(request, client_address)
        except socket.error as e:
            if e.errno == 32:
                self.logger.debug("%s: Client disconnected while answering it's request.",
                                                client_address, exc_info=True)
            else:
                raise


    def daemonize(self, user=0, group=0):
        # do the UNIX double-fork magic, see Stevens' "Advanced
        # Programming in the UNIX Environment" for details (ISBN 0201563177)
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("Fork failed (#1): %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        # chdir -> don't prevent unmounting...
        os.chdir("/")

        # Create new process group with the process as leader
        os.setsid()

        # Set user/group depending on params
        if group:
            os.setregid(getgrnam(group)[2], getgrnam(group)[2])
        if user:
            os.setreuid(getpwnam(user)[2], getpwnam(user)[2])

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("Fork failed (#2): %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()

        si = os.open("/dev/null", os.O_RDONLY)
        so = os.open("/dev/null", os.O_WRONLY)
        os.dup2(si, 0)
        os.dup2(so, 1)
        os.dup2(so, 2)
        os.close(si)
        os.close(so)

        self.logger.debug("Daemonized with PID %d." % os.getpid())


    def register_signal_handlers(self):
        signal.signal(2,  self.signal_handler) # INT
        signal.signal(3,  self.signal_handler) # QUIT
        signal.signal(15, self.signal_handler) # TERM


    def signal_handler(self, signum, stack_frame):
        raise SignalReceived(signum)


    def register_for_ccu_events(self):
        if not Config.ccu_enabled:
            return

        thread = threading.Thread(target=self._do_register_for_ccu_events)
        thread.daemon = True
        thread.start()


    def _do_register_for_ccu_events(self):
        self.ccu.events.init()
        self.ccu.devices.on_value_updated(self._on_value_updated)
        self._events_initialized = True


    def _on_value_updated(self, updated_param):
        self.events.add_event({
            "time"           : updated_param.last_updated,
            "time_changed"   : updated_param.last_changed,
            "param"          : updated_param,
            "value"          : updated_param.value,
            "formated_value" : "%s" % updated_param,
        })



class RequestHandler(wsgiref.simple_server.WSGIRequestHandler, utils.LogMixin):
    def log_message(self, fmt, *args):
        self.logger.debug("%s %s" % (self.client_address[0], fmt%args))


    def log_exception(self, exc_info):
        self.logger.error("Unhandled exception: %s" % traceback.format_exc())



class Events(object):
    def __init__(self):
        self._events = []
        self._num_events_total = 0


    def add_event(self, event_dict):
        self._num_events_total += 1
        self._events.append(event_dict)
        if len(self._events) > 1000:
            self._events.pop(0)


    @property
    def events(self):
        return self._events


    @property
    def num_events_total(self):
        return self._num_events_total
