from simpletr64.devicetr64 import DeviceTR64

try:
    # noinspection PyCompatibility
    from urlparse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urllib.parse import urlparse


class Wan(DeviceTR64):
    """Class to get various WAN information's of a device which supports ``urn:dslforum-org:service:WAN*``.

    The class supports devices which supports ``urn:dslforum-org:service:WAN* namespace``. Unless the
    device is a AVM Fritz product the object needs to load the device definitions with
    :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions` before the usage of any of the methods.
    For a Fritz product :meth:`~simpletr64.DeviceTR64.setupTR64Device` can be called also this might not be future
    compatible. Also a device might not support all of the actions. This class does not implement all of the actions
    of this namespace, please check the SCPD definitions if you miss some functionality. This library provides some
    tools to gather the needed information's.

    All WAN actions ask for a interface id, this depends on the device if the counting starts with 0 or 1.
    Rarely a device supports more than one interface but for consistency reasons you can choose your interface.

    .. seealso::

        Baseclass: :class:`~simpletr64.DeviceTR64`

        :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`, :meth:`~simpletr64.DeviceTR64.loadSCPD`,
        :meth:`~simpletr64.DeviceTR64.setupTR64Device`

        The tools which have been provided with this library shows good use of the full library.
    """

    serviceTypeLookup = {
        "getLinkInfo": "urn:dslforum-org:service:WANDSLInterfaceConfig:",
        "getLinkProperties": "urn:dslforum-org:service:WANCommonInterfaceConfig:",
        "getADSLInfo": "urn:dslforum-org:service:WANDSLLinkConfig:",
        "getEthernetLinkStatus": "urn:dslforum-org:service:WANEthernetLinkConfig:",
        "getByteStatistic": "urn:dslforum-org:service:WANCommonInterfaceConfig:",
        "getPacketStatistic": "urn:dslforum-org:service:WANCommonInterfaceConfig:",
        "getConnectionInfo": "urn:dslforum-org:service:WANIPConnection:",
        "setEnable": "urn:dslforum-org:service:WANDSLLinkConfig:",
        "requestConnection": "urn:dslforum-org:service:WANIPConnection:1",
        "terminateConnection": "urn:dslforum-org:service:WANIPConnection:1"
    }

    def __init__(self, hostname, port=49000, protocol="http"):
        """Initialize the object.

        :param str hostname: hostname or IP address of the device
        :param int port: there is no default port usually, it is different per vendor. Default port for fritz.box is
            49000 and when encrypted 49443
        :param str protocol: protocol is either http or https
        :rtype: Wan
        """
        DeviceTR64.__init__(self, hostname, port, protocol)

    @staticmethod
    def createFromURL(urlOfXMLDefinition):
        """Factory method to create a DeviceTR64 from an URL to the XML device definitions.

        :param str urlOfXMLDefinition:
        :return: the new object
        :rtype: Wan
        """
        url = urlparse(urlOfXMLDefinition)

        if not url.port:
            if url.scheme.lower() == "https":
                port = 443
            else:
                port = 80
        else:
            port = url.port

        return Wan(url.hostname, port, url.scheme)

    @staticmethod
    def getServiceType(method):
        """For a given method name return the service type which supports it.

        :param method: the method name to lookup
        :return: the service type or None, an interface id needs to be added to this
        :rtype: str
        """
        if method in Wan.serviceTypeLookup.keys():
            return Wan.serviceTypeLookup[method]
        return None

    def getLinkInfo(self, wanInterfaceId=1, timeout=1):
        """Execute GetInfo action to get basic WAN link information's.

        :param int wanInterfaceId: the id of the WAN device
        :param float timeout: the timeout to wait for the action to be executed
        :return: basic WAN link information's
        :rtype: WanLinkInfo
        """
        namespace = Wan.getServiceType("getLinkInfo") + str(wanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetInfo", timeout=timeout)

        return WanLinkInfo(results)

    def getLinkProperties(self, wanInterfaceId=1, timeout=1):
        """Execute GetCommonLinkProperties action to get WAN link properties.

        :param int wanInterfaceId: the id of the WAN device
        :param float timeout: the timeout to wait for the action to be executed
        :return: WAN link properties
        :rtype: WanLinkProperties
        """
        namespace = Wan.getServiceType("getLinkProperties") + str(wanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetCommonLinkProperties", timeout=timeout)

        return WanLinkProperties(results)

    def getADSLInfo(self, wanInterfaceId=1, timeout=1):
        """Execute GetInfo action to get basic ADSL information's.

        :param int wanInterfaceId: the id of the WAN device
        :param float timeout: the timeout to wait for the action to be executed
        :return: ADSL informations.
        :rtype: ADSLInfo
        """
        namespace = Wan.getServiceType("getADSLInfo") + str(wanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetInfo", timeout=timeout)

        return ADSLInfo(results)

    def getEthernetLinkStatus(self, wanInterfaceId=1, timeout=1):
        """Execute GetEthernetLinkStatus action to get the status of the ethernet link.

        :param int wanInterfaceId: the id of the WAN device
        :param float timeout: the timeout to wait for the action to be executed
        :return: status of the ethernet link
        :rtype: str
        """
        namespace = Wan.getServiceType("getEthernetLinkStatus") + str(wanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetEthernetLinkStatus", timeout=timeout)

        return results["NewEthernetLinkStatus"]

    def getByteStatistic(self, wanInterfaceId=1, timeout=1):
        """Execute GetTotalBytesSent&GetTotalBytesReceived actions to get WAN statistics.

        :param int wanInterfaceId: the id of the WAN device
        :param float timeout: the timeout to wait for the action to be executed
        :return: a tuple of two values, total bytes sent and total bytes received
        :rtype: list[int]
        """
        namespace = Wan.getServiceType("getByteStatistic") + str(wanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetTotalBytesSent", timeout=timeout)
        results2 = self.execute(uri, namespace, "GetTotalBytesReceived", timeout=timeout)

        return [int(results["NewTotalBytesSent"]),
                int(results2["NewTotalBytesReceived"])]

    def getPacketStatistic(self, wanInterfaceId=1, timeout=1):
        """Execute GetTotalPacketsSent&GetTotalPacketsReceived actions to get WAN statistics.

        :param int wanInterfaceId: the id of the WAN device
        :param float timeout: the timeout to wait for the action to be executed
        :return: a tuple of two values, total packets sent and total packets received
        :rtype: list[int]
        """
        namespace = Wan.getServiceType("getPacketStatistic") + str(wanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetTotalPacketsSent", timeout=timeout)
        results2 = self.execute(uri, namespace, "GetTotalPacketsReceived", timeout=timeout)

        return [int(results["NewTotalPacketsSent"]),
                int(results2["NewTotalPacketsReceived"])]

    def getConnectionInfo(self, wanInterfaceId=1, timeout=1):
        """Execute GetInfo action to get WAN connection information's.

        :param int wanInterfaceId: the id of the WAN device
        :param float timeout: the timeout to wait for the action to be executed
        :return: WAN connection information's.
        :rtype: ConnectionInfo
        """
        namespace = Wan.getServiceType("getConnectionInfo") + str(wanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetInfo", timeout=timeout)

        return ConnectionInfo(results)

    def setEnable(self, status, wanInterfaceId=1, timeout=1):
        """Set enable status for a WAN interface, be careful you don't cut yourself off.

        :param bool status: enable or disable the interface
        :param int wanInterfaceId: the id of the WAN interface
        :param float timeout: the timeout to wait for the action to be executed
        """
        namespace = Wan.getServiceType("setEnable") + str(wanInterfaceId)
        uri = self.getControlURL(namespace)

        if status:
            setStatus = 1
        else:
            setStatus = 0

        self.execute(uri, namespace, "SetEnable", timeout=timeout, NewEnable=setStatus)

    def requestConnection(self, wanInterfaceId=1, timeout=1):
        """Request the connection to be established

        :param int wanInterfaceId: the id of the WAN interface
        :param float timeout: the timeout to wait for the action to be executed
        """
        namespace = Wan.getServiceType("requestConnection") + str(wanInterfaceId)
        uri = self.getControlURL(namespace)

        self.execute(uri, namespace, "RequestConnection", timeout=timeout)

    def terminateConnection(self, wanInterfaceId=1, timeout=1):
        """Terminate the connection

        :param int wanInterfaceId: the id of the WAN interface
        :param float timeout: the timeout to wait for the action to be executed
        """
        namespace = Wan.getServiceType("terminateConnection") + str(wanInterfaceId)
        uri = self.getControlURL(namespace)

        self.execute(uri, namespace, "ForceTermination", timeout=timeout)


class WanLinkInfo:
    """A container class for WAN link information's."""

    def __init__(self, results):
        """Initialize an object

        :param results: action results of an GetInfo action
        :type results: dict[str,str]
        :rtype: WanLinkInfo
        """
        self.__enabled = bool(int(results["NewEnable"]))
        self.__status = results["NewStatus"]
        self.__dataPath = results["NewDataPath"]
        self.__upstreamCurrentRate = int(results["NewUpstreamCurrRate"])
        self.__downstreamCurrentRate = int(results["NewDownstreamCurrRate"])
        self.__upstreamMaxRate = int(results["NewUpstreamMaxRate"])
        self.__downstreamMaxRate = int(results["NewDownstreamMaxRate"])
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
        """Return if the WAN link is enabled.

        :return: if the WAN link is enabled.
        :rtype: bool
        """
        return self.__enabled

    @property
    def status(self):
        """Return the WAN link status.

        :return: the WAN link status.
        :rtype: str
        """
        return self.__status

    @property
    def dataPath(self):
        """Return .... what

        :return:
        :rtype: str
        """
        return self.__dataPath

    @property
    def upstreamCurrentRate(self):
        """Return the current upstream rate of the WAN link.

        :return: the current upstream rate of the WAN link.
        :rtype: int
        """
        return self.__upstreamCurrentRate

    @property
    def downStreamCurrentRate(self):
        """Return the current downstream rate of the WAN link.

        :return: the current downstream rate of the WAN link.
        :rtype: int
        """
        return self.__downstreamCurrentRate

    @property
    def upstreamMaxRate(self):
        """Return the maximal upstream rate of the WAN link.

        :return: the maximal upstream rate of the WAN link.
        :rtype: int
        """
        return self.__upstreamMaxRate

    @property
    def downstreamMaxRate(self):
        """Return the maximal downstream rate of the WAN link.

        :return: the maximal downstream rate of the WAN link.
        :rtype: int
        """
        return self.__downstreamMaxRate


class ADSLInfo:
    """A container class for ADSL link information's."""

    def __init__(self, results):
        """Initialize an object

        :param results: action results of an GetInfo action
        :type results: dict[str,str]
        :rtype: ADSLInfo
        """
        self.__enabled = bool(int(results["NewEnable"]))
        self.__status = results["NewLinkStatus"]
        self.__linkType = results["NewLinkType"]
        self.__destinationAddress = results["NewDestinationAddress"]
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
        """Return if the ADSL interface is enabled.

        :return: if the ADSL interface is enabled.
        :rtype: bool
        """
        return self.__enabled

    @property
    def status(self):
        """Return the status for the ADSL interface.

        :return: the status for the ADSL interface.
        :rtype: str
        """
        return self.__status

    @property
    def linkType(self):
        """Return the link type for the ADSL interface.

        :return: Return the link type for the ADSL interface.
        :rtype: str
        """
        return self.__linkType

    @property
    def destinationAddress(self):
        """Return the destination address of the ADSL interface.

        :return: the destination address of the ADSL interface.
        :rtype: str
        """

        return self.__destinationAddress


class WanLinkProperties:
    """A container class for WAN link properties."""

    def __init__(self, results):
        """Initialize an object

        :param results: action results of an GetCommonLinkProperties action
        :type results: dict[str,str]
        :rtype: WanLinkProperties
        """
        self.__accessType = results["NewWANAccessType"]
        self.__upstreamMaxBitRate = int(results["NewLayer1UpstreamMaxBitRate"])
        self.__downstreamMaxBitRate = int(results["NewLayer1DownstreamMaxBitRate"])
        self.__linkStatus = results["NewPhysicalLinkStatus"]
        self.__raw = results

    @property
    def raw(self):
        """Return the raw results which have been used to initialize the object.

        :return: the raw results
        :rtype: dict[str,str]
        """
        return self.__raw

    @property
    def accessType(self):
        """Return the access type of the WAN link.

        :return: the access type of the WAN link.
        :rtype: str
        """
        return self.__accessType

    @property
    def linkStatus(self):
        """Return the WAN link status.

        :return: the WAN link status.
        :rtype: str
        """
        return self.__linkStatus

    @property
    def upstreamMaxBitRate(self):
        """Return the maximum bit rate for the upstream on this WAN link.

        :return: the maximum bit rate for the upstream on this WAN link.
        :rtype: int
        """
        return self.__upstreamMaxBitRate

    @property
    def downstreamMaxBitRate(self):
        """Return the maximum bit rate for the downstream on this WAN link.

        :return: the maximum bit rate for the downstream on this WAN link.
        :rtype: int
        """
        return self.__downstreamMaxBitRate


class ConnectionInfo:
    """A container class for WAN connection information's."""

    def __init__(self, results):
        """Initialize an object

        :param results: action results of an GetInfo action
        :type results: dict[str,str]
        :rtype: ConnectionInfo
        """
        self.__enabled = bool(int(results["NewEnable"]))
        self.__status = results["NewConnectionStatus"]
        self.__type = results["NewConnectionType"]
        self.__name = results["NewName"]
        self.__uptime = int(results["NewUptime"])
        self.__connectionType = results["NewConnectionType"]
        self.__lastConnectionError = results["NewLastConnectionError"]
        self.__natEnabled = bool(int(results["NewNATEnabled"]))
        self.__externalIPaddress = results["NewExternalIPAddress"]
        self.__dnsServers = results["NewDNSServers"]
        self.__macAddress = results["NewMACAddress"]
        self.__dnsEnabled = bool(int(results["NewDNSEnabled"]))
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
        """Return if WAN connection is enabled.

        :return: if WAN connection is enabled.
        :rtype: bool
        """
        return self.__enabled

    @property
    def status(self):
        """Return the status of the WAN connection.

        :return: the status of the WAN connection.
        :rtype: str
        """
        return self.__status

    @property
    def type(self):
        """Return the type of the WAN connection.

        :return: the type of the WAN connection.
        :rtype: str
        """
        return self.__type

    @property
    def name(self):
        """Return the name of the WAN connection.

        :return: the name of the WAN connection.
        :rtype: str
        """
        return self.__name

    @property
    def uptime(self):
        """Return the uptime of the WAN connection.

        :return: the uptime of the WAN connection.
        :rtype: int
        """
        return self.__uptime

    @property
    def lastConnectionError(self):
        """Return the last connection error of the WAN connection.

        :return: the last connection error of the WAN connection.
        :rtype: str
        """
        return self.__lastConnectionError

    @property
    def connectionType(self):
        """Return the type of the WAN connection.

        :return: the type of the WAN connection.
        :rtype: str
        """
        return self.__connectionType

    @property
    def natEnabled(self):
        """Return if NAT is enabled for the WAN connection.

        :return: if NAT is enabled for the WAN connection.
        :rtype: bool
        """
        return self.__natEnabled

    @property
    def externalIPaddress(self):
        """Return the external IP address of the WAN connection.

        :return: the external IP address of the WAN connection.
        :rtype: str
        """
        return self.__externalIPaddress

    @property
    def dnsServers(self):
        """Return the list of DNS servers for the WAN connection.

        :return: the list of DNS servers for the WAN connection.
        :rtype: str
        """
        return self.__dnsServers

    @property
    def macAddress(self):
        """Return the MAC address of the WAN device.

        :return: the MAC address of the WAN device.
        :rtype: str
        """
        return self.__macAddress

    @property
    def dnsEnabled(self):
        """Return if DNS is enabled for the WAN connection.

        :return: if DNS is enabled for the WAN connection.
        :rtype: bool
        """
        return self.__dnsEnabled
