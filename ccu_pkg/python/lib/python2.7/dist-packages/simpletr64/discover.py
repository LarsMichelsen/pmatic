
from simpletr64.devicetr64 import DeviceTR64

try:
    # noinspection PyCompatibility
    from httplib import HTTPResponse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from http.client import HTTPResponse

try:
    # noinspection PyCompatibility
    from urlparse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urllib.parse import urlparse

import socket
import xml.etree.ElementTree as ET
from io import BytesIO

import requests


class Discover:
    """This class provides several static methods to discover UPnP devices.

    """

    def __init__(self):
        raise ValueError("This class can not be instantiated.")

    @staticmethod
    def discover(service="ssdp:all", timeout=1, retries=2, ipAddress="239.255.255.250", port=1900):
        """Discovers UPnP devices in the local network.

        Try to discover all devices in the local network which do support UPnP. The discovery process can fail
        for various reasons and it is recommended to do at least two discoveries, which you can specify with the
        ``retries`` parameter.

        The default ``service`` parameter tries to address all devices also if you know which kind of service type
        you are looking for you should set it as some devices do not respond or respond differently otherwise.

        :param service: the service type or list of service types of devices you look for
        :type service: str or list[str]
        :param float timeout: the socket timeout for each try
        :param int retries: how often should be a discovery request send
        :param str ipAddress: the multicast ip address to use
        :param int port: the port to use
        :return: a list of DiscoveryResponse objects or empty if no device was found
        :rtype: list[DiscoveryResponse]

        Example:
          ::

            results = discover()
            for result in results:
                print("Host: " + result.locationHost + " Port: " + result.locationPort + " Device definitions: " + \\
                    result.location)

        .. seealso::

            :class:`~simpletr64.DiscoveryResponse`, :meth:`~simpletr64.Discover.discoverParticularHost`
        """

        socket.setdefaulttimeout(timeout)

        messages = []

        if isinstance(service, str):
            services = [service]
        elif isinstance(service, list):
            services = service

        for service in services:
            message = 'M-SEARCH * HTTP/1.1\r\nMX: 5\r\nMAN: "ssdp:discover"\r\nHOST: ' + \
                      ipAddress + ':' + str(port) + '\r\n'
            message += "ST: " + service + "\r\n\r\n"
            messages.append(message)

        responses = {}

        for _ in range(retries):

            # setup the socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

            # noinspection PyAssignmentToLoopOrWithParameter
            for _ in range(2):

                # send the messages with different service types
                for message in messages:
                    # send message more often to make sure all devices will get it
                    sock.sendto(message.encode('utf-8'), (ipAddress, port))

            while True:
                try:
                    # read the message until timeout
                    data = sock.recv(1024)
                except socket.timeout:
                    break
                else:
                    # no time out, read the response data and create response object
                    response = DiscoveryResponse(data)
                    # filter duplicated responses
                    responses[response.location] = response

        # return a list of all responses
        return list(responses.values())

    @staticmethod
    def discoverParticularHost(host, service="ssdp:all", deviceDefinitionURL=None, timeout=1, retries=2,
                               ipAddress="239.255.255.250", port=1900, proxies=None):
        """Discover a particular host and find the best response.

        This tries to find the most specific discovery result for the given host. Only the discovery result contains
        the URL to the XML tree which initializes the device definition. If an URL is already known it should be
        provided to avoid additional latency for a broader first device discovery.
        This method also do some magic to find the best result for the given host as UPnP devices behave sometimes
        strangely. This call is costly the result if any should be cached.

        :param str host: the host to find
        :param service: the service type or list of service types if known to search for
        :type service: str or list[str]
        :param str deviceDefinitionURL: if provided it is used to skip a first device discovery
        :param float timeout: the time to wait for each retry
        :param int retries: the amount of times how often the device is tried to discover
        :param str ipAddress: the multicast ip address to discover devices
        :param int port: the port to discover devices
        :param str proxies: proxy definition as defined here:
            `Proxy definition <http://docs.python-requests.org/en/latest/user/advanced/#proxies>`_
        :return: If the device have been found the response is returned otherwise None
        :rtype: DiscoveryResponse
        :raises ValueError: if problems with reading or parsing the xml device definition occurs
        :raises requests.exceptions.ConnectionError: when the device definitions can not be downloaded
        :raises requests.exceptions.ConnectTimeout: when download time out

        Example:
          ::

            proxies = {"http": "http://localhost:8888"}
            result = discoverParticularHost("192.168.0.1", proxies=proxies)
            if result is not None:
                print("Host: " + result.locationHost + " Port: " + result.locationPort + " Device definitions: " + \\
                    result.location)

        .. seealso::

            :class:`~simpletr64.DiscoveryResponse`, :meth:`~simpletr64.Discover.discover`
        """

        # get all IP addresses for the given host
        ipResults = socket.getaddrinfo(host, 80)

        if len(ipResults) == 0:
            return None

        ipAddresses = []

        # remember all ip addresses for the given host
        for ipAdrTupple in ipResults:
            ipAddresses.append(ipAdrTupple[4][0])

        bestPick = None
        services = []

        if deviceDefinitionURL is None:
            # no xml definition given, so lets search for one

            # search for all devices first
            discoverResults = Discover.discover(service=service, timeout=timeout, retries=retries,
                                                ipAddress=ipAddress, port=port)

            for result in discoverResults:
                if result.locationHost in ipAddresses:
                    # now we found a result for that host, pick the best service type if multiple results for the host
                    # are found
                    if Discover.rateServiceTypeInResult(result) > Discover.rateServiceTypeInResult(bestPick):
                        bestPick = result

                    # remember all services
                    if result.service not in services:
                        services.append(result.service)

            if bestPick is None:
                return None
        else:
            # create response with given parameter
            bestPick = DiscoveryResponse.create(deviceDefinitionURL, service=service)

        # some routers do not advice their TR64 capabilities but their UPnp which is only a subset of actions.
        # Try to find out if the given XML definition path will give us a better service type.
        # load xml definition

        # some devices response differently without a User-Agent
        headers = {"User-Agent": "Mozilla/5.0; SimpleTR64-3"}

        request = requests.get(bestPick.location, proxies=proxies, headers=headers, timeout=float(timeout))

        if request.status_code != 200:
            errorStr = DeviceTR64._extractErrorString(request)
            raise ValueError('Could not get CPE definitions for "' + bestPick.location + '": ' +
                             str(request.status_code) + ' - ' + request.reason + " -- " + errorStr)

        # parse xml
        try:
            root = ET.fromstring(request.text.encode('utf-8'))
        except Exception as e:
            raise ValueError("Could not parse CPE definitions for '" + bestPick.location + "': " + str(e))

        # find the first deviceType in the document tree
        for element in root.getiterator():
            # check if element tag name ends on deviceType, skip XML namespace
            if element.tag.lower().endswith("devicetype"):

                serviceFound = element.text

                # remember the service found if it does not exist yet
                if serviceFound not in services:
                    services.append(serviceFound)

                # create a specific service just to check if we found it already
                serviceFound = serviceFound.replace("schemas-upnp-org", "dslforum-org")

                # test if we already have the best service type then we dont need to do an other discovery request
                if serviceFound == bestPick.service:
                    return bestPick

                for service in services:
                    # we search for the specific device tyoe version as of specified in TR64 protocol.
                    # some devices returns different results depending on the given service type, so lets be
                    # very specific
                    specificService = service.replace("schemas-upnp-org", "dslforum-org")

                    if specificService not in services:
                        services.append(specificService)

                # we do an other discovery request with more specific service/device type
                discoverResultsSpecific = Discover.discover(service=services, timeout=float(timeout), retries=retries,
                                                            ipAddress=ipAddress, port=port)

                # iterate through all results to find the most specific one
                evenBetterPick = None

                for specificResult in discoverResultsSpecific:
                    if specificResult.locationHost in ipAddresses:
                        if Discover.rateServiceTypeInResult(specificResult) > \
                                Discover.rateServiceTypeInResult(evenBetterPick):
                            evenBetterPick = specificResult

                if evenBetterPick is not None:
                    # best we could find
                    return evenBetterPick

                # we found first deviceType tag in the XML structure, no need to go further
                break

        if deviceDefinitionURL is not None:
            # we created our own response, so no result found
            return None

        # we found only an unspecific result, return it anyway
        return bestPick

    @staticmethod
    def rateServiceTypeInResult(discoveryResponse):
        """Gives a quality rating for a given service type in a result, higher is better.

        Several UpnP devices reply to a discovery request with multiple responses with different service type
        announcements. To find the most specific one we need to be able rate the service types against each other.
        Usually this is an internal method and just exported for convenience reasons.

        :param DiscoveryResponse discoveryResponse: the response to rate
        :return: a rating of the quality of the given service type
        :rtype: int
        """
        if discoveryResponse is None:
            return 0

        serviceType = discoveryResponse.service

        if serviceType.startswith("urn:dslforum-org:device"):
            return 11
        if serviceType.startswith("urn:dslforum-org:service"):
            return 10
        if serviceType.startswith("urn:dslforum-org:"):
            return 9
        if serviceType.startswith("urn:schemas-upnp-org:device"):
            return 8
        if serviceType.startswith("urn:schemas-upnp-org:service"):
            return 7
        if serviceType.startswith("urn:schemas-upnp-org:"):
            return 6
        if serviceType.startswith("urn:schemas-"):  # other schemas, schema-any-com for example
            return 5
        if serviceType.startswith("urn:"):
            return 4
        if serviceType.startswith("upnp:rootdevice"):
            return 3
        if serviceType.startswith("uuid:"):  # no service, just the uuid given
            return 2
        return 1


class DiscoveryResponse(HTTPResponse):
    """A helper class for results of discovery requests.

    .. seealso::

        :meth:`~simpletr64.Discover.discover`, :meth:`~simpletr64.Discover.discoverParticularHost`
    """
    def __init__(self, data):
        """Initialize a new object.

        :param data: a stream of data which contain a discovery response in the HTTP format.
        :type data: str or list[bytes] or list[int]
        :rtype: DiscoveryResponse
        """

        # create a fake socket which is needed by the base class to initialize.
        # initialize the base class
        HTTPResponse.__init__(self, DiscoveryResponse._FakeSocket(data), 1)

        # turn off any debugging in the base class
        self.debuglevel = 0

        # let the base class parse the input
        self.begin()

        # set dedicated properties from the discovery response headers
        self.__location = self.getheader("location")
        self.__usn = self.getheader("usn")
        self.__service = self.getheader("st")

        # parse the location URL
        urlParts = urlparse(self.location)

        self.__locationProtocol = urlParts.scheme.lower()

        self.__locationPath = urlParts.path
        self.__locationHost = urlParts.hostname

        # set the right port depending on if a port was given or the given protocol
        if urlParts.port:
            self.__locationPort = urlParts.port
        else:
            if self.__locationProtocol == "https":
                self.__locationPort = 443
            else:
                self.__locationPort = 80

    class _FakeSocket:
        """An internal dummy socket class which emulates some interfaces."""
        def __init__(self, data):
            self._file = BytesIO(DiscoveryResponse._FakeSocket.getBytes(data))

        # noinspection PyUnusedLocal
        def makefile(self, *args, **kwargs):
            """Emulate a socket interface.
            :param args: ignore
            :param kwargs: ignore
            """
            return self._file

        @staticmethod
        def getBytes(obj):
            """Converts a given object to a list of bytes.

            :param obj: object to convert
            :type obj: str or list[bytes] or list[int]
            :raises TypeError: if type of given object do not match
            """
            if isinstance(obj, str):
                return obj.encode('utf-8')
            elif isinstance(obj, bytes):
                return obj
            elif isinstance(obj, int):
                return bytes([obj])
            else:
                raise TypeError("Invalid argument: " + str(type(obj)))

    @staticmethod
    def create(location, service="uuid:none", usn="none"):
        """Factory method to create an DiscoverResponse object with dedicated parameters.

        :param str location: the location of the new object
        :param str service: which service should be used
        :param str usn: the device id which should be used
        :return: the newly created object
        :rtype: DiscoveryResponse
        """
        return DiscoveryResponse("HTTP/1.1 200 OK\r\nLOCATION: " + location + "\r\nST: " + service +
                                 "\r\nUSN: " + usn + "\r\n\r\n")

    @property
    def location(self):
        """Return the location of the discovery response which points to the device definitions.

        The location usually is a full URL to an XML device definition, example
        ``http://192.168.0.24:49000/tr64desc.xml``

        :return: the location
        :rtype: str
        """
        return self.__location

    @property
    def usn(self):
        """Return the device id of the device which responded.

        Example: ``uuid:739f2419-bccb-40e7-8e6c-BC254222D5C4::urn:dslforum-org:device:InternetGatewayDevice:1``

        :return: the device id
        :rtype: str
        """
        return self.__usn

    @property
    def service(self):
        """Returns the service which was announced by the device response.

        Example: ``urn:dslforum-org:device:InternetGatewayDevice:1``

        :return: the service type
        :rtype: str
        """
        return self.__service

    @property
    def locationProtocol(self):
        """Returns the protocol of the location URL.

        For the given example: ``http://192.168.0.24:49000/tr64desc.xml`` the result would be ``http``

        :return: the extracted protocol of the location URL
        :rtype: str

        .. seealso: location
        """
        return self.__locationProtocol

    @property
    def locationPath(self):
        """Returns the URI path of the location URL.

        For the given example: ``http://192.168.0.24:49000/tr64desc.xml`` the result would be ``/tr64desc.xml``

        :return: the extracted URI of the location URL
        :rtype: str

        .. seealso: location
        """
        return self.__locationPath

    @property
    def locationHost(self):
        """Returns the host or IP address  of the location URL.

        For the given example: ``http://192.168.0.24:49000/tr64desc.xml`` the result would be ``192.168.0.24``

        :return: the extracted host part of the location URL
        :rtype: str

        .. seealso: location
        """
        return self.__locationHost

    @property
    def locationPort(self):
        """Returns the port of the location URL.

        For the given example: ``http://192.168.0.24:49000/tr64desc.xml`` the result would be ``49000``. If no
        port was given the port is assumed based on the protocol.

        :return: the extracted port of the location URL
        :rtype: int

        .. seealso: location
        """
        return self.__locationPort

    # we override this method only to make sure it appears in the documentation
    def getheaders(self):
        """Return all headers from the response

        This gives the ability to access all HTTP headers of a discovery response.

        :return: dict[str, str]
        """
        return HTTPResponse.getheaders(self)

    def __str__(self):
        return "LOC: " + self.location + " SRV: " + self.service

    def __repr__(self):
        return str(self)
