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
    from builtins import object # pylint:disable=redefined-builtin
except ImportError:
    pass

import time
import socket
import threading

try:
    # Python 2
    from urlparse import urlparse
except ImportError:
    # Python 3+
    from urllib.parse import urlparse

try:
    # Python 2
    from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
except ImportError:
    # Python 3+
    from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler


import pmatic.api
import pmatic.utils as utils
from pmatic.exceptions import PMException, PMConnectionError


class EventXMLRPCServer(SimpleXMLRPCServer, threading.Thread):
    """Implements SimpleXMLRPCServer executed in a separate thread"""
    def __init__(self, *args, **kwargs):
        SimpleXMLRPCServer.__init__(self, *args, **kwargs)
        threading.Thread.__init__(self)
        self.daemon = True

        # Register system.listMethods, system.methodHelp and system.methodSignature
        self.register_introspection_functions()
        # Allow multicalls
        self.register_multicall_functions()


    def system_listMethods(self, interface_id): # pylint:disable=unused-argument
        """Wrap the standard system_listMethods of SimpleXMLRPCDispatcher. This is needed
        because the CCU sends an argument (the interface_id) which is not handled by the
        default system_listMethods() method."""
        return super(EventXMLRPCServer, self).system_listMethods()


    def run(self):
        """Starts listening for requests in the thread."""
        self.serve_forever()


    def stop(self):
        """Tells the SimpleXMLRPCServer to stop serving."""
        self.shutdown()
        self.server_close()



class EventXMLRPCRequestHandler(SimpleXMLRPCRequestHandler, utils.LogMixin):
    """HTTP request handler for the XML-RPC API requests."""
    def log_message(self, format_str, *args):
        """Logger messages for the web server logs."""
        self.logger.debug("%s - - [%s] %s\n", self.address_string(),
                                            self.log_date_time_string(),
                                            format_str%args)



class EventListener(utils.LogMixin, utils.CallbackMixin):
    """Manages events received from the CCU XML-RPC API.

    This class can tell the CCU to send status update events to pmatic
    using it's XML-RPC API. The EventListener registers with the CCU
    to get status updates. The CCU then synchronizes the known objects
    with pmatic and starts sending status updates. These status updates
    are then received by this class and handed over to the :class:`pmatic.entities.Device`
    objects managed by the central :class:`CCU` object to update their
    current state information.

    The first argument *ccu* must be the :class:`CCU` instance to be associated
    with this object.

    The optional argument *listen_address* can be set to exactly tell
    the CCU to which host address and TCP port to send it's XML-RPC calls. This
    defaults to the host address of your local system and TCP port ``9123``. You
    are free to set another port of your choice by specifying it as tuple of two
    elements like e.g. ``("", 1337)``. The first element needs to contain the host
    address of the system pmatic is running on and is normally automatically gathered.
    But you can also set a fixed address if you like.

    The second optional argument *interface_id* is an identifier which needs to be
    unique on your local system at any time. As far as I can tell this is only
    relevant when you plan to register multiple :class:`EventListener` objects at
    the same time, on the same system and the same network port. If you start multiple
    listeners within the same proccess the identifier is automatically made unique and
    don't need to be set.
    """

    _ident = 0

    @classmethod
    def _next_id(cls):
        """Each event listener gets a unique ID which is used to register with the CCU."""
        this_id = cls._ident
        cls._ident += 1
        return this_id


    def __init__(self, ccu, listen_address=None, interface_id=None):
        super(EventListener, self).__init__()
        self._ccu         = ccu
        self._server      = None
        self._initialized = False
        self._init_callbacks(["value_updated", "value_changed"])
        self._init_listen_address(listen_address)
        self._init_interface_id(interface_id)


    def _init_listen_address(self, listen_address):
        """Parses the listen_address provided by the user."""
        if listen_address is None:
            # listen on all interfaces. Use port 9123 by default.
            self._listen_address = ('', 9123)

        elif isinstance(listen_address, tuple) and len(listen_address) == 2:
            self._listen_address = listen_address

        else:
            raise PMException("listen_address needs to be a tuple of two "
                              "elements (address, port): %r" % (listen_address, ))


    def _init_interface_id(self, interface_id):
        """Initializes the interface ID of this object."""
        if interface_id is not None:
            if utils.is_string(interface_id):
                self._interface_id = interface_id
            else:
                raise PMException("interface_id has to be of type string")
        else:
            self._interface_id = "pmatic-%d" % EventListener._next_id()


    @property
    def rpc_server_url(self):
        """Contains the URL the RPC server of this EventListener is listening on.

        This URL is the URL sent to the CCU by :meth:`.init`."""
        address = self._listen_address
        if address[0] == "":
            # This EventListener is configured to listen on all interfaces. That
            # makes things flexible. But the drawback is that we don't know which
            # URL we should tell the CCU to send it's events to. Find out!
            address = (self._find_listen_address_to_reach_ccu(), address[1])

        return "http://%s:%d" % address


    def init(self):
        """Initializes this objects RPC server and registers with the CCU.

        This method opens the XML-RPC server on the configured *listen_address* and
        sends an API call to the CCU to register the just started XML-RPC server.
        The CCU is then sending XLM-RPC messages to this server.
        """
        try:
            self._start_rpc_server()
            self._register_with_ccu()
            self._initialized = True
        except:
            self.close()
            raise


    @property
    def initialized(self):
        """Is set to true when the XML-RPC have been started and registered with the CCU."""
        return self._initialized


    def _start_rpc_server(self):
        """Starts listening for incoming XML-RPC messages from CCU."""
        self.logger.debug("Start listening for events on %s TCP %s" %
                            (self._listen_address[0] or "*", self._listen_address[1]))
        self._server = EventXMLRPCServer(self._listen_address,
                                         requestHandler=EventXMLRPCRequestHandler)
        self._server.register_instance(EventHandler(self._ccu, self))
        self._server.start()


    def _register_with_ccu(self):
        """Registers the RPC server of this EventListener object with the CCU.

        After executing this method the CCU will contact the RPC server of
        this EventListener and send events to the server.
        """
        result = self._ccu.api.interface_init(interface="BidCos-RF",
            url=self.rpc_server_url, interfaceId=self._interface_id)
        if not result:
            raise PMConnectionError("Failed to register with the XML-RPC API of the CCU.")
        elif result == True:
            self.logger.debug("Successfully registered event listener with CCU")


    def _find_listen_address_to_reach_ccu(self):
        """Determines the host address to tell the CCU to send it's messages to.

        When the listen_address is either not set or set to an empty string this makes
        the XML-RPC server listen on all local interfaces / addresses. But the drawback
        is that we don't know which URL we should tell the CCU to send it's events to.

        This method determines the address to tell the CCU.

        When the script is executed on the CCU it returns "127.0.0.1". Otherwise it creats
        a socket and opens a connection to the CCU address (which is used by self._ccu.api)
        and port 80. Then it knows which local IP address has been used to communicate
        with the CCU. This address is then returned.
        """
        if isinstance(self._ccu.api, pmatic.api.LocalAPI):
            return "127.0.0.1"

        ccu_address = urlparse(self._ccu.api.address).hostname

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1) # wait for 1 second for the connect.
        try:
            s.connect((ccu_address, 80))
            address = s.getsockname()[0]
            s.close()
            return address
        except socket.error as e:
            raise PMException("Unable to detect the address to listen on for XML-RPC "
                              "messages from the CCU (%s). You might fix this by explicitly "
                              "providing the parameter listen_address=([ADDRESS], [PORT]) "
                              "to pmatic.events.init()." % e)


    def close(self):
        """Stops listening for XML-RPC messages and terminates the local XML-RPC server."""
        if self._server:
            self.logger.info("Stop listening for events")
            self._server.stop()
            self._server.join()
            self._server = None
        self._initialized = False


    def __del__(self):
        """When object is removed, the close() method is called."""
        self.close()


    def wait(self, timeout=None):
        """Waits for the event listener to terminate.

        This is useful to let your code stay idle (for some time) and
        just wait for incoming events from the CCU.

        When a timeout is configured this method returns when the listener
        terminates (for some reason) or the timeout happens.

        This method returns ``True`` when the timeout happened and the listener
        is still alive or ``False`` when the listener has been terminated.
        """
        try:
            while self._server.is_alive():
                time.sleep(0.1)
                if timeout is not None:
                    timeout -= 0.1
                    if timeout <= 0:
                        break
        except KeyboardInterrupt:
            self._server.stop()
            self._server.join()
        return self._server.is_alive()


    def on_value_changed(self, func):
        """Register a function to be called each time any value of a device is changed."""
        self.register_callback("value_changed", func)


    def on_value_updated(self, func):
        """Register a function to be called each time a value of any device is updated."""
        self.register_callback("value_updated", func)


    def callback(self, cb_name, *args, **kwargs):
        """Execute all registered callbacks for this event."""
        self._callback(cb_name, *args, **kwargs)



class EventHandler(utils.LogMixin, object):
    """Handles incoming XML-RPC calls."""
    def __init__(self, ccu, listener):
        self._ccu = ccu
        self.listener = listener
        super(EventHandler, self).__init__()


    def _dispatch(self, method, params):
        """Central entry point for all calls.

        It does not let exceptions through to the caller. The exceptions
        are all catched and logged.
        """
        try:
            func = getattr(self, method)
        except AttributeError:
            raise PMException("Requested method %r is not implemented." % method)

        try:
            return func(*params)
        except Exception:
            self.logger.error("Exception in XML-RPC call %s%r:",
                                method, tuple(params), exc_info=True)
            return False


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
    def event(self, interface_id, address, value_key, value): # pylint:disable=unused-argument
        """Receives an event from the CCU and applies the update."""
        self.logger.debug("[EVENT] %s %s = %r", address, value_key, value)

        try:
            obj = self._ccu.devices.get_device_or_channel_by_address(address)
        except KeyError:
            self.logger.info("[EVENT] %s Ignoring event for unknown device" % address)
            return True

        param = obj.values[value_key]

        value_changed = param.set_from_api(value)

        self.listener.callback("value_updated", param)
        if value_changed:
            self.listener.callback("value_changed", param)

        return True


    # Diese  Methode  gibt  alle  der  Logikschicht  bekannten Geräte für den Schnittstellen-Prozess
    # mit der Id interface_id in Form von Gerätebeschreibungen zurück. Damit kann der
    # Schnittstellenprozess durch Aufruf von  new Devices() und deleteDevices() einen Abgleich
    # vornehmen. Damit  das  funktioniert,  muss  sich  die  Logikschicht diese  Informationen
    # zumindest teilweise merken. Es ist dabei ausreichend, wenn je weils die Member ADDRESS
    # und VERSION einer DeviceDescription gesetzt sind.
    def listDevices(self, interface_id): # pylint:disable=unused-argument
        """The CCU asks for all already known devices. Send back the address and description
        version."""
        devices = []

        # Don't fetch new new devices here. Use the already known ones. The CCU will inform
        # us about the ones we don't know yet.
        for device in self._ccu.devices.already_initialized_devices.values():
            devices.append({"ADDRESS": device.address, "VERSION": device.version})
            for channel in device.channels:
                devices.append({"ADDRESS": channel.address, "VERSION": channel.version})

        return devices


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
    def newDevices(self, interface_id, dev_descriptions): # pylint:disable=unused-argument
        """The CCU informs about new devices. Creates objects known for them."""
        self.logger.debug("[NEW DEVICES] Got %d new devices/channels", len(dev_descriptions))

        # Perform the following steps to make the data equal to the ccu.devices._device_specs
        # dict data structure which is fetched by the JSON API. To make the internal code of
        # pmatic simpler it is better to normalize this here where it is clear where which kind
        # of data comes from.
        #
        # The goal is to make this data totally equal (TODO Create a test for this):
        #import pprint
        #file("/tmp/event-devices.txt", "w").write(pprint.pformat(sorted(devices.items())))
        #specs = self._ccu.api.DeviceSpecs(self._ccu.api)
        #file("/tmp/api-devices.txt", "w").write(pprint.pformat(sorted(specs.items())))
        def normalize_spec(d):
            for key in d.keys():
                val = d.pop(key)
                if isinstance(val, list):
                    for index, item in enumerate(val):
                        val[index] = item.decode("utf-8")

                elif utils.is_byte_string(val):
                    val = val.decode("utf-8")

                new_key = key.lower().decode("utf-8")

                if new_key in [ "aes_active", "roaming" ]:
                    val = val == 1

                elif new_key == "updatable":
                    val = "%d" % val

                elif new_key in [ "link_source_roles", "link_target_roles" ]:
                    val = val.split()

                elif new_key in [ "rf_address", "rx_mode" ]:
                    continue

                d[new_key] = val
            return d

        devices = {}

        for spec in dev_descriptions:
            spec = normalize_spec(spec)
            if not spec.get("parent"):
                try:
                    del spec["parent"]
                except KeyError:
                    pass
                devices[spec["address"]] = spec
            else:
                channels = devices[spec["parent"]].setdefault("channels", [])
                channels.append(spec)

        for device_dict in devices.values():
            self._ccu.devices.add_from_low_level_dict(device_dict)

        # As we just received all devices from the CCU mark the devices as initialized
        # in the CCU object. This saves one Interface.listDevices call when accessing
        # the "self._ccu.devices.devices" for the first time.
        self._ccu.devices.initialized = True

        return True


    # Mit   dieser   Methode   wird   der   Logikschicht   mitgeteilt,   dass   Geräte   im
    # Schnittstellenprozess gelöscht wurden.  Der Parameter interface_id
    #  gibt die id des Schnittstellenprozesses an, zu dem das Gerät gehört.
    # Der  Parameter addresses ist  ein  Array,  das  die  Adressen  der
    # gelöschten  Geräte enthält.
    # FIXME: Only handling device addresses. Can we get channels here?
    def deleteDevices(self, interface_id, addresses): # pylint:disable=unused-argument
        """A device has been removed from the CCU. Reflect that change."""
        self.logger.debug("[DELETE DEVICES] Delete %d devices/channels", len(addresses))
        for address in addresses:
            self._ccu.devices.delete(address)
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
    # FIXME: To be implemented.
    def updateDevices(self, interface_id, address, hint): # pylint:disable=unused-argument
        """The CCU wants to update the parameters of a device."""
        self.logger.debug("[UPDATE DEVICES] Update for device %s (%d)", address, hint)
        return True
