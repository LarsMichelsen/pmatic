from simpletr64.devicetr64 import DeviceTR64

try:
    # noinspection PyCompatibility
    from urlparse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urllib.parse import urlparse


class System(DeviceTR64):
    """Class to get various System information's of a device which supports ``urn:dslforum-org:service:DeviceInfo:1``
    and ``urn:dslforum-org:service:Time:1``.

    The class supports devices which supports ``urn:dslforum-org:service:Time:1`` and
    ``urn:dslforum-org:service:DeviceInfo:1``
    namespace. Unless the device is a AVM Fritz product the object needs to load the device definitions with
    :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions` before the usage of any of the methods.
    For a Fritz product :meth:`~simpletr64.DeviceTR64.setupTR64Device` can be called also this might not be future
    compatible. Also a device might not support all of the actions. This class does not implement all of the actions
    of this namespace, please check the SCPD definitions if you miss some functionality. This library provides some
    tools to gather the needed information's.

    .. seealso::

        Baseclass: :class:`~simpletr64.DeviceTR64`

        :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`, :meth:`~simpletr64.DeviceTR64.loadSCPD`,
        :meth:`~simpletr64.DeviceTR64.setupTR64Device`

        The tools which have been provided with this library shows good use of the full library.
    """

    serviceTypeLookup = {
        "getSystemInfo": "urn:dslforum-org:service:DeviceInfo:1",
        "reboot": "urn:dslforum-org:service:DeviceConfig:1",
        "getTimeInfo": "urn:dslforum-org:service:Time:1",
        "softwareUpdateAvailable": "urn:dslforum-org:service:UserInterface:1"
    }

    def __init__(self, hostname, port=49000, protocol="http"):
        """Initialize the object.

        :param str hostname: hostname or IP address of the device
        :param int port: there is no default port usually, it is different per vendor. Default port for fritz.box is
            49000 and when encrypted 49443
        :param str protocol: protocol is either http or https
        :rtype: System
        """
        DeviceTR64.__init__(self, hostname, port, protocol)

    @staticmethod
    def createFromURL(urlOfXMLDefinition):
        """Factory method to create a DeviceTR64 from an URL to the XML device definitions.

        :param str urlOfXMLDefinition:
        :return: the new object
        :rtype: System
        """
        url = urlparse(urlOfXMLDefinition)

        if not url.port:
            if url.scheme.lower() == "https":
                port = 443
            else:
                port = 80
        else:
            port = url.port

        return System(url.hostname, port, url.scheme)

    @staticmethod
    def getServiceType(method):
        """For a given method name return the service type which supports it.

        :param method: the method name to lookup
        :return: the service type or None
        :rtype: str
        """
        if method in System.serviceTypeLookup.keys():
            return System.serviceTypeLookup[method]
        return None

    def getSystemInfo(self, timeout=1):
        """Execute GetInfo action to get information's about the System on the device.

        :return: information's about the System on the device.
        :rtype: SystemInfo
        """
        namespace = System.getServiceType("getSystemInfo")
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetInfo", timeout=timeout)

        return SystemInfo(results)

    def reboot(self, timeout=1):
        """Reboot the device"""
        namespace = System.getServiceType("reboot")
        uri = self.getControlURL(namespace)

        self.execute(uri, namespace, "Reboot", timeout=timeout)

    def getTimeInfo(self, timeout=1):
        """Execute GetInfo action to get information's about the time on the device.

        :return: information's about the time on the device.
        :rtype: TimeInfo
        """
        namespace = System.getServiceType("getTimeInfo")
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetInfo", timeout=timeout)

        return TimeInfo(results)

    def softwareUpdateAvailable(self, timeout=1):
        """Returns if a software update is available

        :return: if a software update is available
        :rtype: bool
        """
        namespace = System.getServiceType("softwareUpdateAvailable")
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetInfo", timeout=timeout)

        return bool(int(results["NewUpgradeAvailable"]))


class TimeInfo:
    """A container class for time information's."""

    def __init__(self, results):
        """Initialize an object

        :param results: action results of an GetInfo action
        :type results: dict[str,str]
        :rtype: TimeInfo
        """
        self.__ntpServer1 = results["NewNTPServer1"]
        self.__ntpServer2 = results["NewNTPServer2"]
        self.__currentLocalTime = results["NewCurrentLocalTime"]
        self.__localTimeZone = results["NewLocalTimeZone"]
        self.__isDaylightSaving = results["NewLocalTimeZoneName"]
        self.__daylightSavingStart = bool(int(results["NewDaylightSavingsUsed"]))
        self.__daylightSavingEnd = results["NewDaylightSavingsStart"]
        self.__localTimeZoneName = results["NewDaylightSavingsEnd"]
        self.__raw = results

    @property
    def raw(self):
        """Return the raw results which have been used to initialize the object.

        :return: the raw results
        :rtype: dict[str,str]
        """
        return self.__raw

    @property
    def ntpServer1(self):
        """Return the first configured NTP server.

        :return: the first configured NTP server.
        :rtype: str
        """
        return self.__ntpServer1

    @property
    def ntpServer2(self):
        """Return the second configured NTP server.

        :return: the second configured NTP server.
        :rtype: str
        """
        return self.__ntpServer2

    @property
    def currentLocalTime(self):
        """Return current local time.

        :return: current local time.
        :rtype: str
        """
        return self.__currentLocalTime

    @property
    def localTimeZone(self):
        """Return the local time zone.

        :return: the local time zone.
        :rtype: str
        """
        return self.__localTimeZone

    @property
    def localTimeZoneName(self):
        """Return the name of the local time zone.

        :return: the name of the local time zone.
        :rtype: str
        """
        return self.__localTimeZoneName

    @property
    def isDaylightSaving(self):
        """Return if it is now day light saving time.

        :return: if it is now day light saving time.
        :rtype: bool
        """
        return self.__isDaylightSaving

    @property
    def daylightSavingStart(self):
        """Return when the day light saving time starts.

        :return: when the day light saving time starts.
        :rtype: str
        """
        return self.__daylightSavingStart

    @property
    def daylightSavingEnd(self):
        """Return when the day light saving time ends.

        :return: when the day light saving time ends.
        :rtype: str
        """
        return self.__daylightSavingEnd


class SystemInfo:
    """A container class for System information's."""

    def __init__(self, results):
        """Initialize an object

        :param results: action results of an GetInfo action
        :type results: dict[str,str]
        :rtype: SystemInfo
        """
        self.__manufactureName = results["NewManufacturerName"]
        self.__modelName = results["NewModelName"]
        self.__description = results["NewDescription"]
        self.__serialNumber = results["NewSerialNumber"]
        self.__softwareVersion = results["NewSoftwareVersion"]
        self.__hwVersion = results["NewHardwareVersion"]
        self.__uptime = int(results["NewUpTime"])
        self.__log = results["NewDeviceLog"]
        self.__raw = results

    @property
    def raw(self):
        """Return the raw results which have been used to initialize the object.

        :return: the raw results
        :rtype: dict[str,str]
        """
        return self.__raw

    @property
    def manufactureName(self):
        """Return the name of the manufacture of the device.

        :return: the name of the manufacture of the device.
        :rtype: str
        """
        return self.__manufactureName

    @property
    def modelName(self):
        """Return the name of the model of the device.

        :return: the name of the model of the device.
        :rtype: str
        """
        return self.__modelName

    @property
    def description(self):
        """Return a description of the device.

        :return: a description of the device
        :rtype: str
        """
        return self.__description

    @property
    def serialNumber(self):
        """Return the serial number of the system.

        :return: the serial number of the system.
        :rtype: str
        """
        return self.__serialNumber

    @property
    def softwareVersion(self):
        """Return the software version of the system.

        :return: the software version of the system.
        :rtype: str
        """
        return self.__softwareVersion

    @property
    def hwVersion(self):
        """Return the hardware version of the system.

        :return: the hardware version of the system.
        :rtype: str
        """
        return self.__hwVersion

    @property
    def uptime(self):
        """Return the uptime of the system.

        :return: the uptime of the system.
        :rtype: int
        """
        return self.__uptime

    @property
    def log(self):
        """Return the last lines in the log file.

        :return: the last lines in the log file.
        :rtype: str
        """
        return self.__log
