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
import signal
import traceback
#import mimetypes
import wsgiref.simple_server
from Cookie import SimpleCookie
from hashlib import sha256

import pmatic
import pmatic.utils as utils
from pmatic.exceptions import UserError, SignalReceived


class Config(object):
    config_path = "/etc/config/addons/pmatic/etc"
    script_path = "/etc/config/addons/pmatic/scripts"
    static_path = "/etc/config/addons/pmatic/manager_static"

# FIXME This handling is only for testing purposes and will be cleaned up soon
if not utils.is_ccu():
    Config.script_path = "/tmp/pmatic-scripts"
    Config.static_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) \
                         + "/manager_static"
    Config.config_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) \
                         + "/etc"


class Html(object):
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
        self.write("<li><a href=\"/\">Scripts</a></li>\n")
        self.write("<li><a href=\"/run\">Live Execution</a></li>\n")
        self.write("<li><a href=\"/config\">Configuration</a></li>\n")
        self.write("<li class=\"right\"><a href=\"https://larsmichelsen.github.io/pmatic/\" "
                   "target=\"_blank\">pmatic %s</a></li>\n" % pmatic.__version__)
        self.write("</ul>\n")


    def is_action(self):
        return bool(self._vars.getvalue("action"))


    def begin_form(self, multipart=None):
        enctype = " enctype=\"multipart/form-data\"" if multipart else ""
        target_url = self.base_url or "/"
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


    def icon_button(self, icon_name, url, title):
        self.write("<a class=\"btn\" href=\"%s\" title=\"%s\">"
                   "<i class=\"fa fa-%s\"></i></a>" % (url, title, icon_name))


    def error(self, text):
        self.message(text, "error")


    def success(self, text):
        self.message(text, "success")


    def message(self, text, cls):
        if cls == "success":
            icon = "check-circle-o"
        else:
            icon = "bomb"
        self.write("<div class=\"message %s\"><i class=\"fa fa-2x fa-%s\"></i> "
                   "%s</div>\n" % (cls, icon, text))


    def h2(self, title):
        self.write("<h2>%s</h2>\n" % title)


    def p(self, content):
        self.write("<p>%s</p>\n" % content)


    def js(self, script):
        self.write("<script type=\"text/javascript\">%s</script>" % script)


    def redirect(self, delay, url):
        self.js("setTimeout(\"location.href = '%s';\", %d);" % (url, delay*1000))



class FieldStorage(cgi.FieldStorage):
    def getvalue(self, key):
        return cgi.FieldStorage.getvalue(self, key.encode("utf-8"))



class PageHandler(object):
    @classmethod
    def pages(cls):
        pages = {}
        for subclass in cls.__subclasses__():
            pages[subclass.base_url] = subclass
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
        secret = file(filepath).read().strip()

        correct_hash = sha256(secret + salt).hexdigest().decode("utf-8")

        return salted_hash == correct_hash


    def __init__(self, environ, start_response):
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
            except UserError as e:
                self.error(e)
            except Exception as e:
                self.error("Unhandled exception: %s" % e)

        try:
            self.process()
        except UserError as e:
            self.error(e)
        except Exception as e:
            self.error("Unhandled exception: %s" % e)

        self.write("\n</div>")
        self.page_footer()

        return self._page


    def ensure_password_is_set(self):
        if not self.is_password_set():
            raise UserError("To be able to access this page you first have to "
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
           or path_info.startswith("/scripts/"):
            file_path = StaticFile.system_path_from_pathinfo(path_info)
            if os.path.exists(file_path):
                return StaticFile


    @classmethod
    def system_path_from_pathinfo(self, path_info):
        if path_info.startswith("/scripts/"):
            return os.path.join(Config.script_path, os.path.basename(path_info))
        else:
            return os.path.join(Config.static_path, path_info.lstrip("/"))


    def _get_content_type(self):
        ext = self._env["PATH_INFO"].split(".")[-1]
        if ext == "css":
            return "text/css; charset=UTF-8"
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


    def process_page(self):
        path_info = self._env["PATH_INFO"]

        if path_info.startswith("/scripts"):
            self._http_headers.append((b"Content-Disposition",
                b"attachment; filename=\"%s\"" % os.path.basename(path_info)))

        self._start_response(self._http_status(200), self._http_headers)

        file_path = StaticFile.system_path_from_pathinfo(self._env["PATH_INFO"])
        return [ l for l in file(file_path) ]



class PageMain(PageHandler, Html, utils.LogMixin):
    base_url = ""

    def title(self):
        return "Manage pmatic Scripts"


    def save_script(self, filename, script):
        if not os.path.exists(Config.script_path):
            os.makedirs(Config.script_path)

        filepath = os.path.join(Config.script_path, filename)
        file(filepath, "w").write(script)
        os.chmod(filepath, 0o755)


    def get_scripts(self):
        try:
            entries = os.listdir(Config.script_path)
        except OSError:
            raise UserError("The script directory %s does not exist." %
                                                    Config.script_path)

        for filename in entries:
            filepath = os.path.join(Config.script_path, filename)
            if os.path.isfile(filepath):
                yield filename


    def action(self):
        self.ensure_password_is_set()
        action = self._vars.getvalue("action")
        if action == "upload":
            self._handle_upload()
        elif action == "delete":
            self._handle_delete()


    def _handle_upload(self):
        if not self._vars.getvalue("script"):
            raise UserError("You need to select a script to upload.")

        filename = self._vars["script"].filename
        script = self._vars["script"].file.read()
        first_line = script.split(b"\n", 1)[0]

        if not first_line.startswith(b"#!/usr/bin/python") \
           and not first_line.startswith(b"#!/usr/bin/env python"):
            raise UserError("The uploaded file does not seem to be a pmatic script.")

        if len(script) > 1048576:
            raise UserError("The uploaded file is too large.")

        self.save_script(filename, script)
        self.success("The script has been uploaded.")


    def _handle_delete(self):
        filename = self._vars.getvalue("script")

        if not filename:
            raise UserError("You need to provide a script name to delete.")

        if filename not in os.listdir(Config.script_path):
            raise UserError("This script does not exist.")

        filepath = os.path.join(Config.script_path, filename)
        os.unlink(filepath)
        self.success("The script has been deleted.")


    def process(self):
        self.ensure_password_is_set()
        self.upload_form()
        self.scripts()


    def upload_form(self):
        self.h2("Upload Script")
        self.p("<p>You can either upload your scripts using this form or "
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
        for filename in self.get_scripts():
            path = os.path.join(Config.script_path, filename)
            last_mod_ts = os.stat(path).st_mtime

            self.write("<tr>")
            self.write("<td>")
            self.icon_button("trash", "?action=delete&script=%s" % filename,
                              "Delete this script")
            self.icon_button("bolt", "/run?script=%s" % filename,
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



class PageLogin(PageHandler, Html, utils.LogMixin):
    base_url = "login"

    def title(self):
        return "Log in to pmatic Manager"


    def action(self):
        password = self._vars.getvalue("password")

        if not password:
            raise UserError("Invalid password.")

        filepath = os.path.join(Config.config_path, "manager.secret")
        secret = file(filepath).read().strip()

        if secret != sha256(password).hexdigest():
            raise UserError("Invalid password.")

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
        self.p("<p>Welcome to the pmatic Manager. Please provide your manager "
               "password to log in.")
        self.write("<div class=\"login\">\n")
        self.begin_form()
        self.password("password")
        self.submit("Log in", "login")
        self.end_form()
        self.write("</div>\n")



class PageConfiguration(PageHandler, Html, utils.LogMixin):
    base_url = "config"

    def title(self):
        return "Configuration of pmatic Manager"


    def action(self):
        action = self._vars.getvalue("action")
        if action == "set_password":
            self._handle_set_password()


    def _handle_set_password(self):
        password = self._vars.getvalue("password")

        if not password:
            raise UserError("You need to provide a password and it must not be empty.")

        if len(password) < 6:
            raise UserError("The password must have a minimal length of 6 characters.")

        filepath = os.path.join(Config.config_path, "manager.secret")
        file(filepath, "w").write(sha256(password).hexdigest()+"\n")
        self.success("The password has been set. You will be redirect to the "
                     "<a href=\"/\">login</a>.")
        self.redirect(2, "/")


    def process(self):
        self.password_form()
        #self.config_form()


    def password_form(self):
        self.h2("Set Manager Password")
        self.p("<p>To make the pmatic manager fully functional, you need to "
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
        # FIXME: Configuration!
        self.end_form()
        self.write("</div>\n")



class Page404(PageHandler, Html, utils.LogMixin):
    base_url = "404"


    def _send_http_header(self):
        self._start_response(self._http_status(404), self._http_headers)


    def title(self):
        return "404 - Page not Found"


    def process(self):
        self.write("The requested page could not be found.")



wsgiref.simple_server.ServerHandler.server_software = 'pmatic-manager'


class Manager(wsgiref.simple_server.WSGIServer, utils.LogMixin):
    def __init__(self, address):
        wsgiref.simple_server.WSGIServer.__init__(
            self, address, RequestHandler)
        self.set_app(self.handle_request)


    def handle_request(self, environ, start_response):
        handler_class = PageHandler.get(environ)
        page = handler_class(environ, start_response)
        return page.process_page()


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



class RequestHandler(wsgiref.simple_server.WSGIRequestHandler, utils.LogMixin):
    def log_message(self, fmt, *args):
        self.logger.info("%s %s" % (self.client_address[0], fmt%args))


    def log_exception(self, exc_info):
        self.logger("Unhandled exception: %s" % traceback.format_exc())
