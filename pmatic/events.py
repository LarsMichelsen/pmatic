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

"""Realizes an event listener to receive events from the CCU XML-RPC API"""

# Relevant docs:
# - http://www.eq-3.de/Downloads/PDFs/Dokumentation_und_Tutorials/HM_XmlRpc_V1_502__2_.pdf

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

import time
import socket
import threading
from SimpleXMLRPCServer import SimpleXMLRPCServer
from urlparse import urlparse

from pmatic.api import LocalAPI
from pmatic import utils
from . import PMException, PMConnectionError


class EventXMLRPCServer(SimpleXMLRPCServer, threading.Thread):
    """Implements SimpleXMLRPCServer executed in a separate thread"""
    def __init__(self, *args, **kwargs):
        SimpleXMLRPCServer.__init__(self, *args, **kwargs)
        threading.Thread.__init__(self)
        self.daemon = True


    def run(self):
        """Starts listening for requests in the thread."""
        self.serve_forever()


    def stop(self):
        """Tells the SimpleXMLRPCServer to stop serving."""
        self.shutdown()



class EventListener(object):
    """Realizes an event listener to receive events from the CCU XML-RPC API"""
    ident = 0

    @classmethod
    def _next_id(cls):
        """Each event listener gets a unique ID which is used to register with the CCU."""
        this_id = cls.ident
        cls.ident += 1
        return this_id


    def __init__(self, API, listen_address=None, interface_id=None):
        self.API = API
        self._init_listen_address(listen_address)
        self._init_interface_id(interface_id)


    def _init_listen_address(self, listen_address):
        """Parses the listen_address provided by the user."""
        if listen_address == None:
            # listen on all interfaces. Use port 9123 by default.
            self._listen_address = ('', 9123)

        elif type(listen_address) == tuple and len(listen_address) == 2:
            self._listen_address = listen_address

        else:
            raise PMException("list_address needs to e a tuple of two "
                              "elements (address, port): %r" % (listen_address, ))


    def _init_interface_id(self, interface_id):
        """Initializes the interface ID of this object."""
        if interface_id != None:
            if utils.is_string(interface_id):
                self._interface_id = interface_id
            else:
                raise PMException("interface_id has to be of type string")
        else:
            self._interface_id = "pmatic-%d" % EventListener._next_id()


    def init(self):
        """Initializes this objects RPC server and registers with the CCU.

        This method opens the XML-RPC server on the configured listen_addres and
        sends an API call to the CCU to register the just started XML-RPC server.
        The CCU is then sending XLM-RPC messages to this server.
        """
        self._start_rpc_server()
        self._register_with_ccu()


    def _start_rpc_server(self):
        """Starts listening for incoming XML-RPC messages from CCU."""
        self._server = EventXMLRPCServer(self._listen_address)
        # Register system.listMethods, system.methodHelp and system.methodSignature
        # FIXME: standard system.listMethods does not seem to be OK for the CCU. Seems as it
        # is sending an argument with the call (I think the interace_id). Seems we need to
        # build it on our own.
        self._server.register_introspection_functions()
        # Allow multicalls
        self._server.register_multicall_functions()
        self._server.register_instance(EventHandler(self.API, self))
        self._server.start()


    def _register_with_ccu(self):
        """Registers the RPC server of this EventListener object with the CCU.

        After executing this method the CCU will contact the RPC server of
        this EventListener and send events to the server.
        """
        result = self.API.interface_init(interface="BidCos-RF",
            url=self.rpc_server_url(), interfaceId=self._interface_id)
        if not result:
            raise PMConnectionError("Failed to register with the XML-RPC API of the CCU.")


    def rpc_server_url(self):
        """Returns the URL the RPC server of this EventListener is listening on."""
        address = self._listen_address
        if address[0] == "":
            # This EventListener is configured to listen on all interfaces. That
            # makes things flexible. But the drawback is that we don't know which
            # URL we should tell the CCU to send it's events to. Find out!
            address = (self._find_listen_address_to_reach_ccu(), address[1])

        return "http://%s:%d" % address


    def _find_listen_address_to_reach_ccu(self):
        """Determines the host address to tell the CCU to send it's messages to.

        When the listen_address is either not set or set to an empty string this makes
        the XML-RPC server listen on all local interfaces / addresses. But the drawback
        is that we don't know which URL we should tell the CCU to send it's events to.

        This method determines the address to tell the CCU.

        When the script is executed on the CCU it returns "127.0.0.1". Otherwise it creats
        a socket and opens a connection to the CCU address (which is used by self.API)
        and port 80. Then it knows which local IP address has been used to communicate
        with the CCU. This address is then returned.
        """
        if isinstance(self.API, LocalAPI):
            return "127.0.0.1"

        ccu_address = urlparse(self.API.address).hostname

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((ccu_address, 80))
            address = s.getsockname()[0]
            s.close()
            return address
        except socket.error:
            raise PMException("Unable to detect the address to listen on for XML-RPC "
                              "messages from the CCU. You might fix this by explicitly "
                              "providing the parameter listen_address=([ADDRESS], [PORT]) "
                              "to pmatic.events.init().")


    def close(self):
        """Stops listening for XML-RPC message."""
        self._server.stop()


    def wait(self, timeout=None):
        """Waits for the event listener to terminate.

        This is useful to let your code stay idle (for some time) and
        just wait for incoming events from the CCU.

        When a timeout is configured this method returns when the listener
        terminates (for some reason) or the timeout happens.

        This method returns True when the timeout happened and the listener
        is still alive or False when the listener has been terminated.
        """
        try:
            while self._server.is_alive():
                time.sleep(0.1)
                if timeout != None:
                    timeout -= 0.1
                    if timeout <= 0:
                        break
        except KeyboardInterrupt:
            self._server.stop()
            self._server.join()
        return self._server.is_alive()


import pprint


class EventHandler(object):
    """Handles incoming XML-RPC calls."""
    def __init__(self, API, listener):
        self.API = API
        self.listener = listener


    # Mit dieser Methode teilt der Schnittstellenprozess der Logikschicht mit, dass sich ein
    # Wert geändert hat oder ein Event (z.B. Tastendruck) empfangen wurde.
    # Der  Parameter interface_id gibt  die  id  des  Schnittstellenprozesses  an,  der  das
    # Event sendet.
    # Der  Parameter address ist  die  Addresse  des  logischen  Gerätes,  zu  dem  der
    # geänderte Wert / das Event gehört.
    # Der Parameter value_key ist der Name des entsprechenden Wertes. Die möglichen
    # Werte  für  value_key  ergeben  sich  aus  der  ParamsetDescription  des  entsprechenden
    # Parameter-Sets „VALUES“.
    # Der Parameter value gibt den neuen Wert bzw. den dem Event zugeordneten Wert an.
    # Der  Datentyp  von value ergibt  sich  aus  der  ParamsetDescription  des
    # Values-Parameter-Sets des entsprechenden logischen Gerätes.
    def event(self, interface_id, address, value_key, value):
        print("EVENT", address, value_key, value)
        return True


    # Diese  Methode  gibt  alle  der  Logikschicht  bekannten Geräte für den Schnittstellen-Prozess
    # mit der Id interface_id in Form von Gerätebeschreibungen zurück. Damit kann der
    # Schnittstellenprozess durch Aufruf von  new Devices() und deleteDevices() einen Abgleich
    # vornehmen. Damit  das  funktioniert,  muss  sich  die  Logikschicht diese  Informationen
    # zumindest teilweise merken. Es ist dabei ausreichend, wenn je weils die Member ADDRESS
    # und VERSION einer DeviceDescription gesetzt sind.
    def listDevices(self, interface_id):
        print("LIST_DEVICES")
        return []


    # Mit  dieser  Methode  wird  der  Logikschicht  mitgeteilt,  dass  neue  Geräte  gefunden
    # wurden.
    # Der Parameter interface_id gibt die id des Schnittstellenprozesses an, zu dem das Gerät
    # gehört.
    # Der Parameter dev_descriptions ist ein Array, das die Beschreibungen der neuen Geräte enthält.
    # Wenn dev_descriptions Geräte enthält, die der Logikschicht bereits beka nnt sind,
    # dann ist davon auszugehen, dass sich z.B. durch ein Firmwareupdate das Verhalten
    # des Gerätes geändert hat. Die Basisplatform muß dann einen Abgleich mit der neuen
    # Beschreibung  durchführen.  Dabei  sollte  die  Konfiguration  des  Gerätes  innerhalb  der
    # Logikschicht so weit wie möglich erhalten bleiben.
    def newDevices(self, interface_id, dev_descriptions):
        pprint.pprint(("NEW_DEVICES", dev_descriptions))
        return True


    # Mit   dieser   Methode   wird   der   Logikschicht   mitgeteilt,   dass   Geräte   im
    # Schnittstellenprozess gelöscht wurden.  Der Parameter interface_id
    #  gibt die id des Schnittstellenprozesses an, zu dem das Gerät gehört.
    # Der  Parameter addresses ist  ein  Array,  das  die  Adressen  der
    # gelöschten  Geräte enthält.
    def deleteDevices(self, interface_id, addresses):
        pprint.pprint(("DELETE_DEVICES", addresses))
        return True


    # Mit dieser Methode wird der Logikschicht mitgeteilt, dass sich an einem Gerät etwas
    # geändert hat.  Der Parameter interface_id gibt die id des Schnittstellenprozesses an, zu dem
    # das Gerät gehört.
    # Der Parameter address ist die Adresse des Gerätes oder des Kanals, auf das sich die
    # Meldung bezieht.
    # Der Parameter hint spezifiziert die Änderung genauer:
    # • UPDATE_HINT_ALL=0
    # Es hat eine nicht weiter spezifizierte Änderung stattgefunden und es sollen daher
    # alle möglichen Änderungen berücksichtigt werden.
    # • UPDATE_HINT_LINKS=1
    # Es hat sich die Anzahl der Verknüpfungspartner geändert.
    #
    # Derzeit  werden  nur  Änderungen  an  den  Verknüpfungspa rtnern  auf  diesem  Weg
    # mitgeteilt.
    def updateDevices(self, interface_id, address, hint):
        pprint.pprint(("UPDATE_DEVICES", address, hint))
        return True



def init(API, **kwargs):
    """Just a small wrapper to realize an interface similar to pmatic.api.init()"""
    return EventListener(API, **kwargs)
