from simpletr64.devicetr64 import DeviceTR64
import xml.etree.ElementTree as ET
import requests

try:
    # noinspection PyCompatibility
    from urlparse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urllib.parse import urlparse


class Fritz(DeviceTR64):
    """Class to get various information's of a Fritz product which has TR64/UpnP enabled

    The class supports various Fritz products which have UpnP enabled.
    Also it is an AVM Fritz product the object should load the device definitions with
    :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions` before the usage of any of the methods.
    As you like to interact with a Fritz product you might use
    :meth:`~simpletr64.DeviceTR64.setupTR64Device` also this might not be future compatible. Also a device might
    not support all of the actions. This class does not implement all of the actions of this namespace, please
    check the SCPD definitions if you miss some functionality. This library provides some tools to gather the
    needed information's.

    All LAN actions ask for a interface id, this depends on the device if the counting starts with 0 or 1.
    Sometimes a device may support more than one LAN interface.

    .. seealso::

        Baseclass: :class:`~simpletr64.DeviceTR64`

        :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`, :meth:`~simpletr64.DeviceTR64.loadSCPD`,
        :meth:`~simpletr64.DeviceTR64.setupTR64Device`

        The tools which have been provided with this library shows good use of the full library.
    """

    serviceTypeLookup = {
        "sendWakeOnLan": "urn:dslforum-org:service:Hosts:",
        "doUpdate": "urn:dslforum-org:service:UserInterface:1",
        "isOptimizedForIPTV": "urn:dslforum-org:service:WLANConfiguration:",
        "setOptimizedForIPTV": "urn:dslforum-org:service:WLANConfiguration:",
        "getCallList": "urn:dslforum-org:service:X_AVM-DE_OnTel:1"
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

        return Fritz(url.hostname, port, url.scheme)

    @staticmethod
    def getServiceType(method):
        """For a given method name return the service type which supports it.

        :param method: the method name to lookup
        :return: the service type or None, an interface id needs to be added to this
        :rtype: str
        """
        if method in Fritz.serviceTypeLookup.keys():
            return Fritz.serviceTypeLookup[method]
        return None

    def sendWakeOnLan(self, macAddress, lanInterfaceId=1, timeout=1):
        """Send a wake up package to a device specified by its MAC address.

        :param str macAddress: MAC address in the form ``38:C9:86:26:7E:38``; be aware that the MAC address might
            be case sensitive, depending on the router
        :param int lanInterfaceId: the id of the LAN interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: the amount of known hosts.
        :rtype: int

        .. seealso:: :meth:`~simpletr64.actions.Lan.getHostDetailsByMACAddress`
        """
        namespace = Fritz.getServiceType("sendWakeOnLan") + str(lanInterfaceId)
        uri = self.getControlURL(namespace)

        self.execute(uri, namespace, "X_AVM-DE_WakeOnLANByMACAddress", timeout=timeout,
                     NewMACAddress=macAddress)

    def doUpdate(self, timeout=1):
        """Do a software update of the Fritz Box if available.

        :param float timeout: the timeout to wait for the action to be executed
        :return: a list of if an update was available and the update state (bool, str)
        :rtype: tuple(bool, str)
        """
        namespace = Fritz.getServiceType("doUpdate")
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "X_AVM-DE_DoUpdate", timeout=timeout)

        return results["NewUpgradeAvailable"], results["NewX_AVM-DE_UpdateState"]

    def isOptimizedForIPTV(self, wifiInterfaceId=1, timeout=1):
        """Return if the Wifi interface is optimized for IP TV

        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed
        :return: if the Wifi interface is optimized for IP TV
        :rtype: bool

        .. seealso:: :meth:`~simpletr64.actions.Fritz.setOptimizedForIPTV`
        """
        namespace = Fritz.getServiceType("isOptimizedForIPTV") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "X_AVM-DE_GetIPTVOptimized", timeout=timeout)

        return bool(int(results["NewX_AVM-DE_IPTVoptimize"]))

    def setOptimizedForIPTV(self, status, wifiInterfaceId=1, timeout=1):
        """Set if the Wifi interface is optimized for IP TV

        :param bool status: set if Wifi interface should be optimized
        :param int wifiInterfaceId: the id of the Wifi interface
        :param float timeout: the timeout to wait for the action to be executed

        .. seealso:: :meth:`~simpletr64.actions.Fritz.isOptimizedForIPTV`
        """
        namespace = Fritz.getServiceType("setOptimizedForIPTV") + str(wifiInterfaceId)
        uri = self.getControlURL(namespace)

        if status:
            setStatus = 1
        else:
            setStatus = 0

        arguments = {"timeout": timeout, "NewX_AVM-DE_IPTVoptimize": setStatus}

        self.execute(uri, namespace, "X_AVM-DE_SetIPTVOptimized", **arguments)

    def getCallList(self, timeout=1):
        """Get the list of phone calls made

        Example of a phone call result:

        ::

            [{'Count': None, 'Name': None, 'CalledNumber': '030868709971', 'Numbertype': 'sip', 'Duration': '0:01',
            'Caller': '015155255399', 'Called': 'SIP: 030868729971', 'Date': '02.01.14 13:14',
            'Device': 'Anrufbeantworter','Path': None, 'Port': '40', 'Type': '1', 'Id': '15'}]

        Types:

        * 1 - answered
        * 2 - missed
        * 3 - outgoing

        :param float timeout: the timeout to wait for the action to be executed
        :return: the list of made phone calls
        :rtype: list[dict[str: str]]
        """
        namespace = Fritz.getServiceType("getCallList")
        uri = self.getControlURL(namespace)

        results = self.execute(uri, namespace, "GetCallList")

        # setup proxies
        proxies = {}
        if self.httpProxy:
            proxies = {"https": self.httpProxy}

        if self.httpsProxy:
            proxies = {"http": self.httpsProxy}

        # get the content
        request = requests.get(results["NewCallListURL"], proxies=proxies, timeout=float(timeout))

        if request.status_code != 200:
            errorStr = DeviceTR64._extractErrorString(request)
            raise ValueError('Could not get CPE definitions "' + results["NewCallListURL"] + '" : ' +
                             str(request.status_code) + ' - ' + request.reason + " -- " + errorStr)

        # parse xml
        try:
            root = ET.fromstring(request.text.encode('utf-8'))
        except Exception as e:
            raise ValueError("Could not parse call list '" + results["NewCallListURL"] + "': " + str(e))

        calls = []

        for child in root.getchildren():
            if child.tag.lower() == "call":

                callParameters = {}

                for callChild in child.getchildren():
                    callParameters[callChild.tag] = callChild.text

                calls.append(callParameters)

        return calls
