from simpletr64.devicetr64 import DeviceTR64
import json

try:
    # noinspection PyCompatibility
    from urlparse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urllib.parse import urlparse


class Wifi(DeviceTR64):
    """Class to get Wifi information's of a device which supports ``urn:dslforum-org:service:WLANConfiguration:X``.

    The class supports devices which supports ``urn:dslforum-org:service:WLANConfiguration:X`` namespace. Unless the
    device is a AVM Fritz product the object needs to load the device definitions with
    :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions` before the usage of any of the methods.
    For a Fritz product :meth:`~simpletr64.DeviceTR64.setupTR64Device` can be called also this might not be future
    compatible. Also a device might not support all of the actions. This class does not implement all of the actions
    of this namespace, please check the SCPD definitions if you miss some functionality. This library provides some
    tools to gather the needed information's.

    All Wifi actions ask for a interface id, this depends on the device if the counting starts with 0 or 1.
    Often a device supports more than one interface as for example to support 2.4 and 5 Ghz.

    .. seealso::

        Baseclass: :class:`~simpletr64.DeviceTR64`

        :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`, :meth:`~simpletr64.DeviceTR64.loadSCPD`,
        :meth:`~simpletr64.DeviceTR64.setupTR64Device`

        The tools which have been provided with this library shows good use of the full library.
    """

    serviceTypeLookup = {
        "getWifiInfo": "urn:dslforum-org:service:WLANConfiguration:",
        "getStatistic": "urn:dslforum-org:service:WLANConfiguration:",
        "getPacketStatistic": "urn:dslforum-org:service:WLANConfiguration:",
        "getTotalAssociations": "urn:dslforum-org:service:WLANConfiguration:",
        "getGenericAssociatedDeviceInfo": "urn:dslforum-org:service:WLANConfiguration:",
        "getSpecificAssociatedDeviceInfo": "urn:dslforum-org:service:WLANConfiguration:",
        "setEnable": "urn:dslforum-org:service:WLANConfiguration:",
        "setChannel": "urn:dslforum-org:service:WLANConfiguration:",
        "setSSID": "urn:dslforum-org:service:WLANConfiguration:"
    }

    def __init__(self, hostname, port=49000, protocol="http"):
        """Initialize the object.

        :param str hostname: hostname or IP address of the device
        :param int port: there is no default port usually, it is different per vendor. Default port for fritz.box is
            49000 and when encrypted 49443
        :param str protocol: protocol is either http or https
        :rtype: Wifi
        """
        DeviceTR64.__init__(self, hostname, port, protocol)

    @staticmethod
    def createFromURL(urlOfXMLDefinition):
        """Factory method to create a DeviceTR64 from an URL to the XML device definitions.

        :param str urlOfXMLDefinition:
        :return: the new object
        :rtype: Wifi
        """
        url = urlparse(urlOfXMLDefinition)

        if not url.port:
            if url.scheme.lower() == "https":
                port = 443
            else:
                port = 80
        else:
            port = url.port

        return Wifi(url.hostname, port, url.scheme)

    @staticmethod
    def getServiceType(method):
        """For a given method name return the service type which supports it.

        :param method: the method name to lookup
        :return: the service type or None, an interface id needs to be added to this
        :rtype: str
        """
        if method in Wifi.serviceTypeLookup.keys():
            return Wifi.serviceTypeLookup[method]
        return None

    def getWifiInfo(self, wifiInterfaceId=1, timeout=1):
        """Execute GetInfo action to get Wifi basic information's.

        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: the basic informations
        :rtype: WifiBasicInfo
        """
        namespace = Wifi.getServiceType("getWifiInfo") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetInfo", timeout=timeout)

        return WifiBasicInfo(results)

    def getStatistic(self, wifiInterfaceId=1, timeout=1):
        """Execute GetStatistics action to get Wifi statistics.

        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: a tuple of two values, total packets sent and total packets received
        :rtype: list[int]
        """
        namespace = Wifi.getServiceType("getStatistic") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetStatistics", timeout=timeout)

        return [int(results["NewTotalPacketsSent"]), int(results["NewTotalPacketsReceived"])]

    def getPacketStatistic(self, wifiInterfaceId=1, timeout=1):
        """Execute GetPacketStatistics action to get Wifi statistics.

        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: a tuple of two values, total packets sent and total packets received
        :rtype: list[int]
        """
        namespace = Wifi.getServiceType("getPacketStatistic") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetPacketStatistics", timeout=timeout)

        return [int(results["NewTotalPacketsSent"]), int(results["NewTotalPacketsReceived"])]

    def getTotalAssociations(self, wifiInterfaceId=1, timeout=1):
        """Execute GetTotalAssociations action to get the amount of associated Wifi clients.

        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: the amount of Wifi clients
        :rtype: int

        .. seealso:: :meth:`~simpletr64.actions.Wifi.getGenericAssociatedDeviceInfo`
        """
        namespace = Wifi.getServiceType("getTotalAssociations") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetTotalAssociations", timeout=timeout)

        return int(results["NewTotalAssociations"])

    def getGenericAssociatedDeviceInfo(self, index, wifiInterfaceId=1, timeout=1):
        """Execute GetGenericAssociatedDeviceInfo action to get detailed information about a Wifi client.

        :param int index: the number of the client
        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: the detailed information's about a Wifi client
        :rtype: WifiDeviceInfo

        .. seealso:: :meth:`~simpletr64.actions.Wifi.getTotalAssociations`
        """
        namespace = Wifi.getServiceType("getGenericAssociatedDeviceInfo") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetGenericAssociatedDeviceInfo", timeout=timeout,
                               NewAssociatedDeviceIndex=index)

        return WifiDeviceInfo(results)

    def getSpecificAssociatedDeviceInfo(self, macAddress, wifiInterfaceId=1, timeout=1):
        """Execute GetSpecificAssociatedDeviceInfo action to get detailed information about a Wifi client.

        :param str macAddress: MAC address in the form ``38:C9:86:26:7E:38``; be aware that the MAC address might
            be case sensitive, depending on the router
        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: the detailed information's about a Wifi client
        :rtype: WifiDeviceInfo

        .. seealso:: :meth:`~simpletr64.actions.Wifi.getGenericAssociatedDeviceInfo`
        """
        namespace = Wifi.getServiceType("getSpecificAssociatedDeviceInfo") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetSpecificAssociatedDeviceInfo", timeout=timeout,
                               NewAssociatedDeviceMACAddress=macAddress)

        return WifiDeviceInfo(results, macAddress=macAddress)

    def setEnable(self, status, wifiInterfaceId=1, timeout=1):
        """Set enable status for a Wifi interface, be careful you don't cut yourself off.

        :param bool status: enable or disable the interface
        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed
        """
        namespace = Wifi.getServiceType("setEnable") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        if status:
            setStatus = 1
        else:
            setStatus = 0

        self.execute(uri, namespace, "SetEnable", timeout=timeout, NewEnable=setStatus)

    def setChannel(self, channel, wifiInterfaceId=1, timeout=1):
        """Set the channel of this Wifi interface

        :param int channel: the channel number
        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed
        """
        namespace = Wifi.getServiceType("setChannel") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        self.execute(uri, namespace, "SetChannel", timeout=timeout, NewChannel=channel)

    def setSSID(self, ssid, wifiInterfaceId=1, timeout=1):
        """Set the SSID (name of the Wifi network)

        :param str ssid: the SSID/wifi network name
        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed
        """
        namespace = Wifi.getServiceType("setChannel") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        self.execute(uri, namespace, "SetChannel", timeout=timeout, NewSSID=ssid)


class WifiDeviceInfo:
    """A container class for Wifi device information's."""

    def __init__(self, results, macAddress=None):
        """Initialize an object

        :param str results: action results of an GetSpecificAssociatedDeviceInfo or
            GetGenericAssociatedDeviceInfo action
        :param str macAddress: in the result for getSpecificAssociatedDeviceInfo is no Mac Address, lets add it again
        :type results: dict[str,str]
        :rtype: WifiDeviceInfo
        """
        if "NewAssociatedDeviceMACAddress" in results.keys():
            self.__macAddress = results["NewAssociatedDeviceMACAddress"]
        else:
            self.__macAddress = macAddress
        self.__ipAddress = results["NewAssociatedDeviceIPAddress"]
        self.__authenticated = bool(int(results["NewAssociatedDeviceAuthState"]))
        self.__raw = results

    @property
    def raw(self):
        """Return the raw results which have been used to initialize the object.

        :return: the raw results
        :rtype: dict[str,str]
        """
        return self.__raw

    @property
    def macAddress(self):
        """Returns the mac address

        :return: the mac address
        :rtype: str
        """
        return self.__macAddress

    @property
    def ipAddress(self):
        """Return the IP address

        :return: the IP address
        :rtype: str
        """
        return self.__ipAddress

    @property
    def authenticated(self):
        """Returns if the client has been authenticated.

        :return: if client is authenticated
        :rtype: bool
        """
        return self.__authenticated

    def __serialize(self):
        out = {"MacAddress": self.__macAddress, "IPAddress": self.__ipAddress, "Authenticated": self.__authenticated}

        return out

    def __str__(self):
        return json.dumps(self.__serialize(), indent=4, sort_keys=True, separators=(',', ': '))

    def __repr__(self):
        return json.dumps(self.__serialize(), indent=None, sort_keys=True, separators=(',', ': '))


class WifiBasicInfo:
    """A container class for Wifi client information's."""
    def __init__(self, results):
        """Initialize an object

        :param results: action results of an GetInfo action
        :type results: dict[str,str]
        :rtype: WifiBasicInfo
        """
        self.__enabled = bool(int(results["NewEnable"]))
        self.__status = results["NewStatus"]
        self.__channel = int(results["NewChannel"])
        self.__ssid = results["NewSSID"]
        self.__beaconType = results["NewBeaconType"]
        self.__macControl = bool(int(results["NewMACAddressControlEnabled"]))
        self.__standard = results["NewStandard"]
        self.__bssid = results["NewBSSID"]
        self.__encryptionMode = results["NewBasicEncryptionModes"]
        self.__authMode = results["NewBasicAuthenticationMode"]
        self.__raw = results

    @property
    def raw(self):
        """Return the raw results which have been used to initialize the object.

        :return: the raw results
        :rtype: dict[str,str]
        """
        return self.__raw

    @property
    def enabled(self):
        """Returns if the Wifi client is enabled.

        :return: if client is enabled.
        :rtype: bool
        """
        return self.__enabled

    @property
    def status(self):
        """Returns the status for the Wifi client.

        :return: the status for the client
        :rtype: str
        """
        return self.__status

    @property
    def channel(self):
        """Returns the used Wifi channel.

        :return: the used Wifi channel
        :rtype: int
        """
        return self.__channel

    @property
    def ssid(self):
        """Return the SSID for the given Wifi client.

        :return: the SSID
        :rtype: str
        """
        return self.__ssid

    @property
    def beaconType(self):
        """Return ... what ever

        :return:
        :rtype: str
        """
        return self.__beaconType

    @property
    def macControl(self):
        """Returns if mac control is activated.

        :return: if mac control is activated
        :rtype: bool
        """
        return self.__macControl

    @property
    def standard(self):
        """Return ... what ever

        :return:
        :rtype: str
        """
        return self.__standard

    @property
    def bssid(self):
        """Returns the BSS id.

        :return: the bss id.
        :rtype: str
        """
        return self.__bssid

    @property
    def encryptionMode(self):
        """Returns the encryption mode.

        :return: the encryption mode
        :rtype: str
        """
        return self.__encryptionMode

    @property
    def authMode(self):
        """Return the authentication mode for the Wifi client.

        :return: the authentication mode for the Wifi client
        :rtype: str
        """
        return self.__authMode
