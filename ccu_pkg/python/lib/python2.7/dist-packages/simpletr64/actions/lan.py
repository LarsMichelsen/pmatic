from simpletr64.devicetr64 import DeviceTR64
import json

try:
    # noinspection PyCompatibility
    from urlparse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urllib.parse import urlparse


class Lan(DeviceTR64):
    """Class to get various LAN information's of a device which supports ``urn:dslforum-org:service:Hosts:1`` and
    ``urn:dslforum-org:service:LAN*``.

    The class supports devices which supports ``urn:dslforum-org:service:LAN*`` and ``urn:dslforum-org:service:Hosts:1``
    namespace. Unless the device is a AVM Fritz product the object needs to load the device definitions with
    :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions` before the usage of any of the methods.
    For a Fritz product :meth:`~simpletr64.DeviceTR64.setupTR64Device` can be called also this might not be future
    compatible. Also a device might not support all of the actions. This class does not implement all of the actions
    of this namespace, please check the SCPD definitions if you miss some functionality. This library provides some
    tools to gather the needed information's.

    All LAN actions ask for a interface id, this depends on the device if the counting starts with 0 or 1.
    Sometimes a device may support more than one LAN interface.

    .. seealso::

        Baseclass: :class:`~simpletr64.DeviceTR64`

        :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`, :meth:`~simpletr64.DeviceTR64.loadSCPD`,
        :meth:`~simpletr64.DeviceTR64.setupTR64Device`

        The tools which have been provided with this library shows good use of the full library.
    """

    serviceTypeLookup = {
        "getAmountOfHostsConnected": "urn:dslforum-org:service:Hosts:",
        "getHostDetailsByIndex": "urn:dslforum-org:service:Hosts:",
        "getHostDetailsByMACAddress": "urn:dslforum-org:service:Hosts:",
        "getEthernetInfo": "urn:dslforum-org:service:LANEthernetInterfaceConfig:",
        "getEthernetStatistic": "urn:dslforum-org:service:LANEthernetInterfaceConfig:",
        "setEnable": "urn:dslforum-org:service:LANEthernetInterfaceConfig:"
    }

    def __init__(self, hostname, port=49000, protocol="http"):
        """Initialize the object.

        :param str hostname: hostname or IP address of the device
        :param int port: there is no default port usually, it is different per vendor. Default port for fritz.box is
            49000 and when encrypted 49443
        :param str protocol: protocol is either http or https
        :rtype: Lan
        """
        DeviceTR64.__init__(self, hostname, port, protocol)

    @staticmethod
    def createFromURL(urlOfXMLDefinition):
        """Factory method to create a DeviceTR64 from an URL to the XML device definitions.

        :param str urlOfXMLDefinition:
        :return: the new object
        :rtype: Lan
        """
        url = urlparse(urlOfXMLDefinition)

        if not url.port:
            if url.scheme.lower() == "https":
                port = 443
            else:
                port = 80
        else:
            port = url.port

        return Lan(url.hostname, port, url.scheme)

    @staticmethod
    def getServiceType(method):
        """For a given method name return the service type which supports it.

        :param method: the method name to lookup
        :return: the service type or None, an interface id needs to be added to this
        :rtype: str
        """
        if method in Lan.serviceTypeLookup.keys():
            return Lan.serviceTypeLookup[method]
        return None

    def getAmountOfHostsConnected(self, lanInterfaceId=1, timeout=1):
        """Execute NewHostNumberOfEntries action to get the amount of known hosts.

        :param int lanInterfaceId: the id of the LAN interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: the amount of known hosts.
        :rtype: int

        .. seealso:: :meth:`~simpletr64.actions.Lan.getHostDetailsByIndex`
        """
        namespace = Lan.getServiceType("getAmountOfHostsConnected") + str(lanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetHostNumberOfEntries", timeout=timeout)

        return int(results["NewHostNumberOfEntries"])

    def getHostDetailsByIndex(self, index, lanInterfaceId=1, timeout=1):
        """Execute GetGenericHostEntry action to get detailed information's of a connected host.

        :param index: the index of the host
        :param int lanInterfaceId: the id of the LAN interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: the detailed information's of a connected host.
        :rtype: HostDetails

        .. seealso:: :meth:`~simpletr64.actions.Lan.getAmountOfHostsConnected`
        """
        namespace = Lan.getServiceType("getHostDetailsByIndex") + str(lanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetGenericHostEntry", timeout=timeout, NewIndex=index)

        return HostDetails(results)

    def getHostDetailsByMACAddress(self, macAddress, lanInterfaceId=1, timeout=1):
        """Get host details for a host specified by its MAC address.

        :param str macAddress: MAC address in the form ``38:C9:86:26:7E:38``; be aware that the MAC address might
            be case sensitive, depending on the router
        :param int lanInterfaceId: the id of the LAN interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: return the host details if found otherwise an Exception will be raised
        :rtype: HostDetails
        """
        namespace = Lan.getServiceType("getHostDetailsByMACAddress") + str(lanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetSpecificHostEntry", timeout=timeout, NewMACAddress=macAddress)

        return HostDetails(results, macAddress=macAddress)

    def getEthernetInfo(self, lanInterfaceId=1, timeout=1):
        """Execute GetInfo action to get information's about the Ethernet interface.

        :param int lanInterfaceId: the id of the LAN interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: information's about the Ethernet interface.
        :rtype: EthernetInfo
        """
        namespace = Lan.getServiceType("getEthernetInfo") + str(lanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetInfo", timeout=timeout)

        return EthernetInfo(results)

    def getEthernetStatistic(self, lanInterfaceId=1, timeout=1):
        """Execute GetStatistics action to get statistics of the Ethernet interface.

        :param int lanInterfaceId: the id of the LAN interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: statisticss of the Ethernet interface.
        :rtype: EthernetStatistic
        """
        namespace = Lan.getServiceType("getEthernetStatistic") + str(lanInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetStatistics", timeout=timeout)

        return EthernetStatistic(results)

    def setEnable(self, status, lanInterfaceId=1, timeout=1):
        """Set enable status for a LAN interface, be careful you don't cut yourself off.

        :param bool status: enable or disable the interface
        :param int lanInterfaceId: the id of the LAN interface
        :param float timeout: the timeout to wait for the action to be executed
        """
        namespace = Lan.getServiceType("setEnable") + str(lanInterfaceId)
        uri = self.getControlURL(namespace)

        if status:
            setStatus = 1
        else:
            setStatus = 0

        self.execute(uri, namespace, "SetEnable", timeout=timeout, NewEnable=setStatus)


class EthernetStatistic:
    """A container class for Ethernet interface statistics."""

    def __init__(self, results):
        """Initialize an object

        :param results: action results of an GetStatistics action
        :type results: dict[str,str]
        :rtype: EthernetStatistic
        """
        self.__bytesSent = int(results["NewBytesSent"])
        self.__bytesReceived = int(results["NewBytesReceived"])
        self.__packetsSent = int(results["NewPacketsSent"])
        self.__packetsReceived = int(results["NewPacketsReceived"])
        self.__raw = results

    @property
    def raw(self):
        """Return the raw results which have been used to initialize the object.

        :return: the raw results
        :rtype: dict[str,str]
        """
        return self.__raw

    @property
    def bytesSent(self):
        """Return the amount of bytes which have been sent.

        :return: the amount of bytes which have been sent.
        :rtype: int
        """
        return self.__bytesSent

    @property
    def bytesReceived(self):
        """Return the amount of bytes which have been received.

        :return: the amount of bytes which have been received.
        :rtype: int
        """
        return self.__bytesReceived

    @property
    def packetsSent(self):
        """Return the amount of packets which have been sent.

        :return: the amount of packets which have been sent.
        :rtype: int
        """
        return self.__packetsSent

    @property
    def packetsReceived(self):
        """Return the amount of packets which have been received.

        :return: the amount of packets which have been received.
        :rtype: int
        """
        return self.__packetsReceived


class EthernetInfo:
    """A container class for Ethernet interface information's."""

    def __init__(self, results):
        """Initialize an object

        :param results: action results of an GetInfo action
        :type results: dict[str,str]
        :rtype: EthernetInfo
        """
        self.__enabled = bool(int(results["NewEnable"]))
        self.__status = results["NewStatus"]
        self.__macAddress = results["NewMACAddress"]
        self.__maxBitRate = results["NewMaxBitRate"]
        self.__duplexMode = results["NewDuplexMode"]
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
        """Return if the interface is enabled.

        :return: if the interface is enabled.
        :rtype: bool
        """
        return self.__enabled

    @property
    def status(self):
        """Return the status of the interface.

        :return: the status of the interface.
        :rtype: str
        """
        return self.__status

    @property
    def macAddress(self):
        """Return the MAC address of the ethernet interface.

        :return: the MAC address of the ethernet interface.
        :rtype: str
        """
        return self.__macAddress

    @property
    def maxBitRate(self):
        """Return the max bit rate of the interface.

        :return: the max bit rate of the interface.
        :rtype: str
        """
        return self.__maxBitRate

    @property
    def duplexMode(self):
        """Return if the Ethernet interface is in half or full duplex mode.

        :return: if the Ethernet interface is in half or full duplex mode.
        :rtype: str
        """
        return self.__duplexMode


class HostDetails:
    """A container class for information's about a LAN connected host."""

    def __init__(self, results, macAddress=None):
        """Initialize an object

        :param results: action results of an GetSpecificHostEntry or GetGenericHostEntry action
        :param str macAddress: in the result for GetSpecificHostEntry is no Mac Address, lets add it again
        :type results: dict[str,str]
        :rtype: HostDetails
        """
        if "NewMACAddress" in results.keys():
            self.__macAddress = results["NewMACAddress"]
        else:
            self.__macAddress = macAddress

        self.__ipAddress = results["NewIPAddress"]
        self.__hostname = results["NewHostName"]
        self.__interface = results["NewInterfaceType"]
        self.__source = results["NewAddressSource"]
        self.__leaseTime = int(results["NewLeaseTimeRemaining"])
        self.__active = bool(int(results["NewActive"]))
        self.__raw = results

    @property
    def raw(self):
        """Return the raw results which have been used to initialize the object.

        :return: the raw results
        :rtype: dict[str,str]
        """
        return self.__raw

    @property
    def ipaddress(self):
        """Return the IP address of the host.

        :return: the IP address of the host.
        :rtype: str
        """
        return self.__ipAddress

    @property
    def hostname(self):
        """Return the name of the host.

        :return: the name of the host.
        :rtype: str
        """
        return self.__hostname

    @property
    def macAddress(self):
        """Return the MAC address of the host.

        :return: the MAC address of the host.
        :rtype: str
        """
        return self.__macAddress

    @property
    def interface(self):
        """Return the interface to which the host is connected.

        :return: the interface to which the host is connected.
        :rtype: str
        """
        return self.__interface

    @property
    def source(self):
        """Return the source where the address of this host was learned.

        :return: the source where the address of this host was learned.
        :rtype str:
        """
        return self.__source

    @property
    def leasetime(self):
        """Return the remaining lease time

        :return: the remaining lease time
        :rtype: int
        """
        return self.__leaseTime

    @property
    def active(self):
        """Return if the host is active.

        :return: if the host is active
        :rtype: bool
        """
        return self.__active

    def __serialize(self):
        out = {"MacAddress": self.__macAddress, "IPAddress": self.__ipAddress,
               "Hostname": self.__hostname, "Interface": self.__interface, "Source": self.__interface,
               "Leasetime": self.__leaseTime, "Active": self.__active}

        return out

    def __str__(self):
        return json.dumps(self.__serialize(), indent=4, sort_keys=True, separators=(',', ': '))

    def __repr__(self):
        return json.dumps(self.__serialize(), indent=None, sort_keys=True, separators=(',', ': '))
