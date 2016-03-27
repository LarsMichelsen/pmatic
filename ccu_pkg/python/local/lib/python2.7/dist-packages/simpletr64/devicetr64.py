import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPDigestAuth

try:
    # noinspection PyCompatibility
    from urlparse import urlparse
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences
    from urllib.parse import urlparse


class DeviceTR64(object):
    """The basic class which represents an UPnP device.

    A device supports methods to gather information's about a hardware device and to execute actions.

    :type __hostname: str
    :type __portnumber: int
    :type __protocol: str
    :type __username: str
    :type __password: str
    :type __httpProxy: str
    :type __httpsProxy: str
    :type __deviceServiceDefinitions: dict[str, dict[str, str]]
    :type __deviceInformations: dict[str, str]
    :type __deviceSCPD: dict[str, dict[str, dict[str, str]]]
    :type __deviceXMLInitialized: bool
    :type __deviceUnknownKeys: dict[str, str]
    """
    def __init__(self, hostname, port=49000, protocol="http"):
        """Initialize a DeviceTR64 object.

        :param str hostname: hostname or IP address of the device
        :param int port: there is no default port usually, it is different per vendor. Default port for fritz.box is
            49000 and when encrypted 49443
        :param str protocol: protocol is either http or https
        :return: an instance of class DeviceTR64
        :rtype: DeviceTR64
        """
        self.__hostname = hostname
        self.__portnumber = port
        self.__protocol = protocol

        self.__username = ""
        self.__password = ""

        self.__httpProxy = ""
        self.__httpsProxy = ""

        self.__deviceServiceDefinitions = {}
        self.__deviceInformations = {}
        self.__deviceSCPD = {}
        self.__deviceXMLInitialized = False
        self.__deviceUnknownKeys = {}

    @staticmethod
    def createFromURL(urlOfXMLDefinition):
        """Factory method to create a DeviceTR64 from an URL to the XML device definitions.

        :param str urlOfXMLDefinition:
        :return: the new DeviceTR64 object
        :rtype: DeviceTR64
        """
        url = urlparse(urlOfXMLDefinition)

        if not url.port:
            if url.scheme.lower() == "https":
                port = 443
            else:
                port = 80
        else:
            port = url.port

        return DeviceTR64(url.hostname, port, url.scheme)

    @property
    def host(self):
        """Return the hostname of this device which was given when instantiated.

        :return: the hostname or ip address of this device
        :rtype: str
        """
        return self.__hostname

    @property
    def port(self):
        """Return the port of this device which was given when instantiated.

        :return: the port of this device
        :rtype: int
        """
        return self.__portnumber

    @property
    def protocol(self):
        """Return the protocol to communicate with this device which was given when instantiated.

        :return: the communication protocol of this device
        :rtype: str
        """
        return self.__protocol

    @property
    def username(self):
        """Property to set and get the username which gets used to authenticate, can be empty.

        :rtype: str
        """
        return self.__username

    @username.setter
    def username(self, username):
        self.__username = username

    @property
    def password(self):
        """Property to set and get the password which gets used to authenticate, if empty it will not be used.

        :rtype: str
        """
        return self.__password

    @password.setter
    def password(self, password):
        self.__password = password

    @property
    def httpProxy(self):
        """Property to get and set the URL to the http proxy which gets used for any http requests.

        :param str proxy: the URL to the http proxy
        :rtype: str

        Example:

        ::

            device = DeviceTR64(...)
            device.httpProxy("http://localhost:8888/")
        """
        return self.__httpProxy

    @httpProxy.setter
    def httpProxy(self, proxy):
        self.__httpProxy = proxy

    @property
    def httpsProxy(self):
        """Property to get and set the URL to the https proxy which gets used for any https requests.

        :param str proxy: the URL to the https proxy
        :rtype: str

        Example:

        ::

            device = DeviceTR64(...)
            device.httpsProxy("https://localhost:8889/")
        """
        return self.__httpsProxy

    @httpsProxy.setter
    def httpsProxy(self, proxy):
        self.__httpsProxy = proxy

    @property
    def deviceServiceDefinitions(self):
        """Returns all known services and dedicated URI's if loaded before.

        If the device definitions have been loaded with :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`
        before this returns all the known service types, otherwise the dict will be empty. The returned dictionary maps
        from a service to an other dictionary which contains usually
        ``controlURL``, ``scpdURL`` and optional ``eventSubURL``:

        * The ``controlURL`` is needed to execute an action in the given service type/namespace.
        * The ``scpdURL`` is a link to an other XML which defines usually the actions for this service type. These
            will be used if :meth:`~simpletr64.DeviceTR64.loadSCPD` is called. Also for some devices it can be empty.
        * The ``eventSubURL`` is optional and can be used to subscribe to certain events, not supported by this lib yet.

        :return: the service type informations of this device
        :rtype: dict[dict[str, str]]

        .. seealso::

            :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`, :meth:`~simpletr64.DeviceTR64.execute`,
            :meth:`~simpletr64.DeviceTR64.loadSCPD`
        """
        return self.__deviceServiceDefinitions

    @property
    def deviceInformations(self):
        """Returns all device informations if loaded before.

        If the device definitions have been loaded with :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions` before
        this methods returns all parsed device information's like device type, device model, manufacture, etc, is empty
        if device information's have not been loaded before.

        Some examples of known information keys:

        ``deviceType, manufacturer, manufacturerURL, modelDescription, modelName, modelNumber, serialNumber``

        Not all keys needs to be present and can be extended any time, still it is a pre defined set and any unknown
        information type will be stored differently and can be obtained via
        :meth:`~simpletr64.DeviceTR64.deviceInformationUnknownKeys`.

        :return: device information's
        :rtype: dict[str, str]

        .. seealso::

            :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`,
            :meth:`~simpletr64.DeviceTR64.deviceInformationUnknownKeys`
        """
        return self.__deviceInformations

    @property
    def deviceInformationUnknownKeys(self):
        """Returns all device information's which are very specific to this device, if loaded with
        :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions` before.

        If the device definitions have been loaded this methods returns all parsed device information's which
        are not standard conform and very specific to the device.

        :return: device specific information's
        :rtype: dict[str, str]

        .. seealso::

            :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`, :meth:`~simpletr64.DeviceTR64.deviceInformations`
        """
        return self.__deviceUnknownKeys

    @property
    def deviceSCPD(self):
        """Returns the loaded SCPD (Service Control Protocol Document)/action definitions.

        Returns all action definitions which have been loaded before with :meth:`~simpletr64.DeviceTR64.loadSCPD`.
        The action definitions are usefull to understand what kind of interaction functionality a device supports.

        The result is structured in the following way:

        ::

            { "<actionName>": { "inParameter": {"name": <>, "variable": <>, "dataType": <>, "defaultValue": <>},
                                "outParameter": {"name": <>, "variable": <>, "dataType": <>, "defaultValue": <>} } }

        The following keys are optional: ``inParameter, outParameter, variable, defaultValue``

        Parameter keys:

        * ``name``: the name of the parameter
        * ``variable``: an optional name to a virtual variable
        * ``dataType``: the data type of this parameter, these are not fixed and depend on the schema and device vendor
        * ``defaultValue``: an optional default value for this parameter

        :return: the loaded action definitions or empty dict if not loaded
        :rtype: dict[str, dict[str, dict[str, str]]]

        .. seealso::

            :meth:`~simpletr64.DeviceTR64.loadSCPD`, :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`
        """
        return self.__deviceSCPD

    def getSCDPURL(self, serviceType, default=None):
        """Returns the SCDP (Service Control Protocol Document) URL for a given service type.

        When the device definitions have been loaded with :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions` this
        method returns for a given service type/namespace the associated URL to the SCDP. If the device definitions
        have not been loaded a default value can be given which gets returned instead. The SCDP specifies all the
        interaction functionality a device provides.

        :param serviceType: the service type to look up for
        :param default: the default return value in case the service type is not found and device definitions are not
            loaded
        :type default: str or None
        :return: the URL/URI
        :rtype: str or None
        :raises ValueError: if the device did load device definitions and the service type is not known.

        .. seealso::

            :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`
        """
        if serviceType in self.__deviceServiceDefinitions.keys():
            return self.__deviceServiceDefinitions[serviceType]["scpdURL"]

        # check if definitions have been loaded, then dont return the default
        if self.__deviceXMLInitialized:
            raise ValueError("Device do not support given serviceType: " + serviceType)

        return default

    def getControlURL(self, serviceType, default=None):
        """Returns the control URL for a given service type.

        When the device definitions have been loaded with :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions` this
        method returns for a given service type/namespace the associated control URL. If the device definitions have
        not been loaded a default value can be given which gets returned instead. The control URL is used to
        execute actions for a dedicated service type/namespace.

        :param serviceType: the service type to look up for
        :param default: the default return value in case the service type is not found and device definitions are not
            loaded
        :type default: str or None
        :return: the URL/URI
        :rtype: str or None
        :raises ValueError: if the device did load device definitions and the service type is not known.

        .. seealso::

            :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`
        """
        if serviceType in self.__deviceServiceDefinitions.keys():
            return self.__deviceServiceDefinitions[serviceType]["controlURL"]

        # check if definitions have been loaded, then dont return the default
        if self.__deviceXMLInitialized:
            raise ValueError("Device do not support given serviceType: " + serviceType)

        return default

    def getEventSubURL(self, serviceType, default=None):
        """Returns the event URL for a given service type.

        When the device definitions have been loaded with :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions` this
        method returns for a given service type/namespace the associated event URL. If the device definitions have
        not been loaded a default value can be given which gets returned instead.

        :param serviceType: the service type to look up for
        :param default: the default return value in case the service type is not found and device definitions are not
            loaded
        :type default: str or None
        :return: the URL/URI
        :rtype: str or None
        :raises ValueError: if the device did load device definitions and the service type is not known.

        .. seealso::

            :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`
        """
        if serviceType in self.__deviceServiceDefinitions.keys():
            return self.__deviceServiceDefinitions[serviceType]["eventSubURL"]

        # check if definitions have been loaded, then dont return the default
        if self.__deviceXMLInitialized:
            raise ValueError("Device do not support given serviceType: " + serviceType)

        return default

    def execute(self, uri, namespace, action, timeout=2, **kwargs):
        """Executes a given action with optional arguments.

        The execution of an action of an UPnP/TR64 device needs more than just the name of an action. It needs the
        control URI which is called to place the action and also the namespace aka service type is needed. The
        namespace defines the scope or service type of the given action, the same action name can appear in different
        namespaces.

        The way how to obtain the needed information's is either through the documentation of the vendor of the
        device. Or through a discovery requests which return's the URL to the root device description XML.

        :param str uri: the control URI, for example ``/upnp/control/hosts``
        :param str namespace: the namespace for the given action, for example ``urn:dslforum-org:service:Hosts:1``
        :param str action: the name of the action to call, for example ``GetGenericHostEntry``
        :param float timeout: the timeout to wait for the action to be executed
        :param kwargs: optional arguments for the given action, depends if the action needs parameter. The arguments
            are given as dict where the key is the parameter name and the value the value of the parameter.
        :type kwargs: dict[str, str]
        :return: returns the results of the action, if any. The results are structured as dict where the key is the
            name of the result argument and the value is the value of the result.
        :rtype: dict[str,str]
        :raises ValueError: if parameters are not set correctly
        :raises requests.exceptions.ConnectionError: when the action can not be placed on the device
        :raises requests.exceptions.ConnectTimeout: when download time out

        Example:

        ::

            device = DeviceTR64(...)
            device.execute("/upnp/control/hosts", "urn:dslforum-org:service:Hosts:1",
                "GetGenericHostEntry", {"NewIndex": 1})
            {'NewActive': '0', 'NewIPAddress': '192.168.0.23', 'NewMACAddress': '9C:20:7B:E7:FF:5F',
                'NewInterfaceType': 'Ethernet', 'NewHostName': 'Apple-TV', 'NewAddressSource': 'DHCP',
                'NewLeaseTimeRemaining': '0'}

        .. seealso::

            `Additional short explanation of the UPnP protocol <http://www.upnp-hacks.org/upnp.html>`_

            :class:`~simpletr64.Discover`, :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`,
            :meth:`~simpletr64.DeviceTR64.loadSCPD`
        """

        if not uri:
            raise ValueError("No action URI has been defined.")

        if not namespace:
            raise ValueError("No namespace has been defined.")

        if not action:
            raise ValueError("No action has been defined.")

        # soap headers
        header = {'Content-Type': 'text/xml; charset="UTF-8"',
                  'Soapaction': '"' + namespace + "#" + action + '"'}

        # build SOAP body
        body = '''<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope
    s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <s:Header/>
    <s:Body>\n'''

        body += "        <u:" + action + ' xmlns="' + namespace + '">\n'

        arguments = {}

        for key in kwargs.keys():
            body += "            <" + key + ">" + str(kwargs[key]) + "</" + key + ">\n"
            arguments[key] = str(kwargs[key])

        body += "        </u:" + action + ">\n"
        body += '''</s:Body>
</s:Envelope>'''

        # setup proxies
        proxies = {}
        if self.__httpsProxy:
            proxies = {"https": self.__httpsProxy}

        if self.__httpProxy:
            proxies = {"http": self.__httpProxy}

        # setup authentication
        auth = None
        if self.__password:
            auth = HTTPDigestAuth(self.__username, self.__password)

        # build the URL
        location = self.__protocol + "://" + self.__hostname + ":" + str(self.port) + uri

        # Post http request
        request = requests.post(location, data=body, headers=header, auth=auth, proxies=proxies, timeout=float(timeout))

        if request.status_code != 200:
            errorStr = DeviceTR64._extractErrorString(request)
            raise ValueError('Could not execute "' + action + str(arguments) + '": ' + str(request.status_code) +
                             ' - ' + request.reason + " -- " + errorStr)

        # parse XML return
        try:
            root = ET.fromstring(request.text.encode('utf-8'))
        except Exception as e:
            raise ValueError("Can not parse results for the action: " + str(e))

        # iterate in the XML structure to get the action result
        actionNode = root[0][0]

        # we need to remove XML namespace for the action node
        namespaceLength = len(namespace) + 2  # add braces
        tag = actionNode.tag[namespaceLength:]

        if tag != (action + "Response"):
            raise ValueError('Soap result structure is wrong, expected action "' + action +
                             'Response" got "' + tag + '".')

        # pack all the received results
        results = {}

        for resultNode in actionNode:
            results[resultNode.tag] = resultNode.text

        return results

    @staticmethod
    def _extractErrorString(request):
        """Extract error string from a failed UPnP call.

        :param request: the failed request result
        :type request: requests.Response
        :return: an extracted error text or empty str
        :rtype: str
        """
        errorStr = ""

        tag = None

        # noinspection PyBroadException
        try:
            # parse XML return
            root = ET.fromstring(request.text.encode('utf-8'))
            tag = root[0][0]
        except:
            # return an empty string as we can not parse the structure
            return errorStr

        for element in tag.getiterator():
            tagName = element.tag.lower()

            if tagName.endswith("string"):
                errorStr += element.text + " "
            elif tagName.endswith("description"):
                errorStr += element.text + " "

        return errorStr

    def setupTR64Device(self, deviceType):
        """Setup actions for known devices.

        For convenience reasons for some devices there is no need to discover/load device definitions before the
        pre defined :doc:`tr64` can be used.

        The following devices are currently supported (please help to extend):

        * fritz.box - Any AVM Fritz Box with the latest software version installed

        :param str deviceType: a known device type
        :raise ValueError: if the device type is not known.

        .. seealso:: :doc:`tr64`
        """

        if deviceType.lower() != "fritz.box":
            raise ValueError("Unknown device type given.")

        self.__deviceServiceDefinitions = {}
        self.__deviceXMLInitialized = False

        # Fritz.box setup
        self.deviceServiceDefinitions["urn:dslforum-org:service:DeviceConfig:1"] = {
            "controlURL": "/upnp/control/deviceconfig"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:ManagementServer:1"] = {
            "controlURL": "/upnp/control/mgmsrv"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:LANConfigSecurity:1"] = {
            "controlURL": "/upnp/control/lanconfigsecurity"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:Time:1"] = {"controlURL": "/upnp/control/time"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:LANHostConfigManagement:1"] = {
            "controlURL": "/upnp/control/lanhostconfigmgm"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:UserInterface:1"] = {
            "controlURL": "/upnp/control/userif"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:DeviceInfo:1"] = {
            "controlURL": "/upnp/control/deviceinfo"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:X_AVM-DE_TAM:1"] = {"controlURL": "/upnp/control/x_tam"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:X_AVM-DE_MyFritz:1"] = {
            "controlURL": "/upnp/control/x_myfritz"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:X_AVM-DE_RemoteAccess:1"] = {
            "controlURL": "/upnp/control/x_remote"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:WLANConfiguration:1"] = {
            "controlURL": "/upnp/control/wlanconfig1"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:WLANConfiguration:3"] = {
            "controlURL": "/upnp/control/wlanconfig3"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:WLANConfiguration:2"] = {
            "controlURL": "/upnp/control/wlanconfig2"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:X_AVM-DE_WebDAVClient:1"] = {
            "controlURL": "/upnp/control/x_webdav"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:WANDSLLinkConfig:1"] = {
            "controlURL": "/upnp/control/wandsllinkconfig1"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:Hosts:1"] = {"controlURL": "/upnp/control/hosts"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:X_VoIP:1"] = {"controlURL": "/upnp/control/x_voip"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:LANEthernetInterfaceConfig:1"] = {
            "controlURL": "/upnp/control/lanethernetifcfg"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:Layer3Forwarding:1"] = {
            "controlURL": "/upnp/control/layer3forwarding"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:WANIPConnection:1"] = {
            "controlURL": "/upnp/control/wanipconnection1"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:X_AVM-DE_OnTel:1"] = {
            "controlURL": "/upnp/control/x_contact"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:WANCommonInterfaceConfig:1"] = {
            "controlURL": "/upnp/control/wancommonifconfig1"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:X_AVM-DE_UPnP:1"] = {
            "controlURL": "/upnp/control/x_upnp"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:WANDSLInterfaceConfig:1"] = {
            "controlURL": "/upnp/control/wandslifconfig1"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:WANPPPConnection:1"] = {
            "controlURL": "/upnp/control/wanpppconn1"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:X_AVM-DE_Storage:1"] = {
            "controlURL": "/upnp/control/x_storage"}
        self.deviceServiceDefinitions["urn:dslforum-org:service:WANEthernetLinkConfig:1"] = {
            "controlURL": "/upnp/control/wanethlinkconfig1"}

    def loadDeviceDefinitions(self, urlOfXMLDefinition, timeout=3):
        """Loads the device definitions from a given URL which points to the root XML in the device.

        This loads the device definitions which is needed in case you like to:

        * get additional information's about the device like manufacture, device type, etc
        * get all support service types of this device
        * use the convenient actions classes part of this library in the actions module

        :param str urlOfXMLDefinition: the URL to the root XML which sets the device definitions.
        :param float timeout: the timeout for downloading
        :raises ValueError: if the XML could not be parsed correctly
        :raises requests.exceptions.ConnectionError: when the device definitions can not be downloaded
        :raises requests.exceptions.ConnectTimeout: when download time out

        .. seealso::

            :meth:`~simpletr64.DeviceTR64.loadSCPD`, :meth:`~simpletr64.DeviceTR64.deviceServiceDefinitions`,
            :meth:`~simpletr64.DeviceTR64.deviceInformations`, :meth:`~simpletr64.DeviceTR64.deviceSCPD`,
            :meth:`~simpletr64.DeviceTR64.getSCDPURL`, :meth:`~simpletr64.DeviceTR64.getControlURL`,
            :meth:`~simpletr64.DeviceTR64.getEventSubURL`
        """

        # setup proxies
        proxies = {}
        if self.__httpsProxy:
            proxies = {"https": self.__httpsProxy}

        if self.__httpProxy:
            proxies = {"http": self.__httpProxy}

        # some devices response differently without a User-Agent
        headers = {"User-Agent": "Mozilla/5.0; SimpleTR64-1"}

        # get the content
        request = requests.get(urlOfXMLDefinition, proxies=proxies, headers=headers, timeout=float(timeout))

        if request.status_code != 200:
            errorStr = DeviceTR64._extractErrorString(request)
            raise ValueError('Could not get CPE definitions "' + urlOfXMLDefinition + '" : ' +
                             str(request.status_code) + ' - ' + request.reason + " -- " + errorStr)

        # parse XML return
        xml = request.text.encode('utf-8')

        return self._loadDeviceDefinitions(urlOfXMLDefinition, xml)

    def _loadDeviceDefinitions(self, urlOfXMLDefinition, xml):
        """Internal call to parse the XML of the device definition.

        :param urlOfXMLDefinition: the URL to the XML device defintions
        :param xml: the XML content to parse
        """

        # extract the base path of the given XML to make sure any relative URL later will be created correctly
        url = urlparse(urlOfXMLDefinition)
        baseURIPath = url.path.rpartition('/')[0] + "/"

        try:
            root = ET.fromstring(xml)
        except Exception as e:
            raise ValueError("Can not parse CPE definitions '" + urlOfXMLDefinition + "': " + str(e))

        self.__deviceServiceDefinitions = {}
        self.__deviceSCPD = {}
        self.__deviceInformations = {'rootURL': urlOfXMLDefinition}
        self.__deviceUnknownKeys = {}
        self.__deviceXMLInitialized = False

        # iterate through all the informations
        self._iterateToFindSCPDElements(root, baseURIPath)
        self.__deviceXMLInitialized = True

    def _iterateToFindSCPDElements(self, element, baseURIPath):
        """Internal method to iterate through device definition XML tree.

        :param element: the XML root node of the device definitions
        :type element: xml.etree.ElementTree.Element
        :param str baseURIPath: the base URL
        """
        for child in element.getchildren():
            tagName = child.tag.lower()
            if tagName.endswith('servicelist'):
                self._processServiceList(child,baseURIPath)

            elif tagName.endswith('devicetype'):
                if "deviceType" not in self.__deviceInformations.keys():
                    self.__deviceInformations["deviceType"] = child.text
            elif tagName.endswith('friendlyname'):
                if "friendlyName" not in self.__deviceInformations.keys():
                    self.__deviceInformations["friendlyName"] = child.text
            elif tagName.endswith('manufacturer'):
                if "manufacturer" not in self.__deviceInformations.keys():
                    self.__deviceInformations["manufacturer"] = child.text
            elif tagName.endswith('manufacturerurl'):
                if "manufacturerURL" not in self.__deviceInformations.keys():
                    self.__deviceInformations["manufacturerURL"] = child.text
            elif tagName.endswith('modeldescription'):
                if "modelDescription" not in self.__deviceInformations.keys():
                    self.__deviceInformations["modelDescription"] = child.text
            elif tagName.endswith('modelname'):
                if "modelName" not in self.__deviceInformations.keys():
                    self.__deviceInformations["modelName"] = child.text
            elif tagName.endswith('modelurl'):
                if "modelURL" not in self.__deviceInformations.keys():
                    self.__deviceInformations["modelURL"] = child.text
            elif tagName.endswith('modelnumber'):
                if "modelNumber" not in self.__deviceInformations.keys():
                    self.__deviceInformations["modelNumber"] = child.text
            elif tagName.endswith('serialnumber'):
                if "serialNumber" not in self.__deviceInformations.keys():
                    self.__deviceInformations["serialNumber"] = child.text
            elif tagName.endswith('presentationurl'):
                if "presentationURL" not in self.__deviceInformations.keys():
                    self.__deviceInformations["presentationURL"] = child.text
            elif tagName.endswith('udn'):
                if "UDN" not in self.__deviceInformations.keys():
                    self.__deviceInformations["UDN"] = child.text
            elif tagName.endswith('upc'):
                if "UPC" not in self.__deviceInformations.keys():
                    self.__deviceInformations["UPC"] = child.text
            elif tagName.endswith('iconlist') or tagName.endswith('specversion'):
                # skip these items
                pass
            else:
                if not tagName.endswith('device') and not tagName.endswith('devicelist'):
                    self.__deviceUnknownKeys[child.tag] = child.text

                self._iterateToFindSCPDElements(child, baseURIPath)

    def _processServiceList(self, serviceList, baseURIPath):
        """Internal method to iterate in the device definition XML tree through the service list.

        :param serviceList: the XML root node of a service list
        :type serviceList: xml.etree.ElementTree.Element
        """

        # iterate through all children in serviceList XML tag
        for service in serviceList.getchildren():

            # has to be a service
            if not service.tag.lower().endswith("service"):
                raise ValueError("Non service tag in servicelist: " + service.tag)

            serviceType = None
            controlURL = None
            scpdURL = None
            eventURL = None

            # go through all the tags of a service and remember the values, ignore unknowns
            for child in service:
                tag = child.tag.lower()

                if tag.endswith("servicetype") or (serviceType is None and tag.endswith("spectype")):
                    serviceType = child.text
                elif tag.endswith("controlurl"):
                    controlURL = str(child.text)

                    # if the url does not start with / (relative) or with a protocol add the base path
                    if not controlURL.startswith("/") and not controlURL.startswith("http"):
                        controlURL = baseURIPath + controlURL

                elif tag.endswith("scpdurl"):

                    scpdURL = str(child.text)

                    # if the url does not start with / (relative) or with a protocol add the base path
                    if not scpdURL.startswith("/") and not scpdURL.startswith("http"):
                        scpdURL = baseURIPath + scpdURL

                elif tag.endswith("eventsuburl"):

                    eventURL = str(child.text)

                    # if the url does not start with / (relative) or with a protocol add the base path
                    if not eventURL.startswith("/") and not eventURL.startswith("http"):
                        eventURL = baseURIPath + eventURL

            # check if serviceType and the URL's have been found
            if serviceType is None or controlURL is None:
                raise ValueError("Service is not complete: " + str(serviceType) + " - " +
                                 str(controlURL) + " - " + str(scpdURL))

            # no service should be defined twice otherwise the old one will be overwritten
            if serviceType in self.__deviceServiceDefinitions.keys():
                raise ValueError("Service type '" + serviceType + "' is defined twice.")

            self.__deviceServiceDefinitions[serviceType] = {"controlURL": controlURL}

            # if the scpd url is defined add it
            if scpdURL is not None:
                self.__deviceServiceDefinitions[serviceType]["scpdURL"] = scpdURL

            # if event url is given we add it as well
            if eventURL is not None:
                self.__deviceServiceDefinitions[serviceType]["eventSubURL"] = eventURL

    def loadSCPD(self, serviceType=None, timeout=3, ignoreFailures=False):
        """Load action definition(s) (Service Control Protocol Document).

        If the device definitions have been loaded via loadDeviceDefinitions() this method loads actions definitions.
        The action definitions are needed if you like to execute an action on a UPnP device. The actions definition
        contains the name of the action, the input and output parameter. You use the definition either with
        execute() or with the actions module of this library which predefines a lot of actions based on the TR64
        standard.

        :param serviceType: the serviceType for which the action definitions should be loaded or all known service
            types if None.
        :param float timeout: the timeout for downloading
        :param bool ignoreFailures: if set to true and serviceType is None any failure in the iteration of loading
            all SCPD will be ignored.
        :raises ValueType: if the given serviceType is not known or when the definition can not be loaded.
        :raises requests.exceptions.ConnectionError: when the scpd can not be downloaded
        :raises requests.exceptions.ConnectTimeout: when download time out

        .. seealso::

            :meth:`~simpletr64.DeviceTR64.loadDeviceDefinitions`, :meth:`~simpletr64.DeviceTR64.deviceSCPD`,
            :doc:`tr64`
        """

        if serviceType is not None:
            self._loadSCPD(serviceType, float(timeout))
        else:
            self.__deviceSCPD = {}
            for serviceType in self.__deviceServiceDefinitions.keys():
                # remove any previous error
                self.__deviceServiceDefinitions[serviceType].pop("error", None)

                try:
                    self._loadSCPD(serviceType, float(timeout))
                except ValueError as e:
                    if not ignoreFailures:
                        # we not ignoring this so rethrow last exception
                        raise
                    else:
                        # add a message in the structure
                        self.__deviceServiceDefinitions[serviceType]["error"] = str(e)

    def _loadSCPD(self, serviceType, timeout):
        """Internal method to load the action definitions.

        :param str serviceType: the service type to load
        :param int timeout: the timeout for downloading
        """

        if serviceType not in self.__deviceServiceDefinitions.keys():
            raise ValueError("Can not load SCPD, no service type defined for: " + serviceType)

        if "scpdURL" not in self.__deviceServiceDefinitions[serviceType].keys():
            raise ValueError("No SCPD URL defined for: " + serviceType)

        # remove actions for given service type
        self.__deviceSCPD.pop(serviceType, None)

        uri = self.__deviceServiceDefinitions[serviceType]["scpdURL"]

        # setup proxies
        proxies = {}
        if self.__httpsProxy:
            proxies = {"https": self.__httpsProxy}

        if self.__httpProxy:
            proxies = {"http": self.__httpProxy}

        # setup authentication
        auth = None
        if self.__password:
            auth = HTTPDigestAuth(self.__username, self.__password)

        # build the URL
        location = self.__protocol + "://" + self.__hostname + ":" + str(self.port) + uri

        # some devices response differently without a User-Agent
        headers = {"User-Agent": "Mozilla/5.0; SimpleTR64-2"}

        # http request
        request = requests.get(location, auth=auth, proxies=proxies, headers=headers, timeout=timeout)

        if request.status_code != 200:
            errorStr = DeviceTR64._extractErrorString(request)
            raise ValueError('Could not load SCPD for "' + serviceType + '" from ' + location + ': ' +
                             str(request.status_code) + ' - ' + request.reason + " -- " + errorStr)

        data = request.text.encode('utf-8')
        if len(data) == 0:
            return

        # parse XML return
        try:
            root = ET.fromstring(data)
        except Exception as e:
            raise ValueError("Can not parse SCPD content for '" + serviceType + "' from '" + location + "': " + str(e))

        actions = {}
        variableTypes = {}
        variableParameterDict = {}

        # iterate through the full XML tree
        for element in root.getchildren():
            tagName = element.tag.lower()

            # go deeper for action lists
            if tagName.endswith("actionlist"):
                # remember the actions and where a specific variable gets referenced
                self._parseSCPDActions(element, actions, variableParameterDict)

            # go deeper for the variable declarations
            elif tagName.endswith("servicestatetable"):
                self._parseSCPDVariableTypes(element, variableTypes)

        # everything have been parsed now merge the variable declarations into the action parameters
        for name in variableParameterDict.keys():
            if name not in variableTypes.keys():
                raise ValueError("Variable reference in action can not be resolved: " + name)

            # iterate through all arguments where this variable have been referenced
            for argument in variableParameterDict[name]:
                # fill in the type of this variable/argument
                argument["dataType"] = variableTypes[name]["dataType"]

                # if the variable declaration includes a default value add it to the action parameter as well
                if "defaultValue" in variableTypes[name].keys():
                    argument["defaultValue"] = variableTypes[name]["defaultValue"]

        self.__deviceSCPD[serviceType] = actions

    def _parseSCPDActions(self, actionListElement, actions, variableParameterDict):
        """Internal method to parse the SCPD definitions.

        :param actionListElement: the action xml element
        :type actionListElement: xml.etree.ElementTree.Element
        :param dict actions: a container to store all actions
        :param dict variableParameterDict: remember where a variable gets referenced
        """

        # go through all action elements in this list
        for actionElement in actionListElement.getchildren():

            action = {}

            # go through all elements in this action
            for inActionElement in actionElement.getchildren():
                tagName = inActionElement.tag.lower()

                if tagName.endswith("name"):
                    # action name
                    action["name"] = inActionElement.text
                elif tagName.endswith("argumentlist"):
                    # parse the arguments of this action
                    for argumentElement in inActionElement.getchildren():

                        argument = {}

                        # go through the argument definition
                        for inArgumentElement in argumentElement.getchildren():
                            tagName = inArgumentElement.tag.lower()

                            if tagName.endswith("name"):
                                # remember the argument name
                                argument["name"] = inArgumentElement.text
                            elif tagName.endswith("direction"):
                                # is it an in or out argument
                                argument["direction"] = inArgumentElement.text
                            elif tagName.endswith("relatedstatevariable"):
                                # remember the argument and safe it under the variable name to dereference later
                                argument["variable"] = inArgumentElement.text

                                if argument["variable"] not in variableParameterDict.keys():
                                    variableParameterDict[argument["variable"]] = []

                                variableParameterDict[argument["variable"]].append(argument)

                        if "name" not in argument.keys():
                            raise ValueError("Parameter definition does not contain a name.")

                        if "direction" not in argument.keys():
                            raise ValueError("Parameter definition does not contain a direction: " + argument["name"])

                        direction = argument["direction"] + "Parameter"

                        # store the actual argument in the action
                        if direction not in action.keys():
                            action[direction] = {}

                        action[direction][argument["name"]] = argument

                        # cleanup, we stored the argument we dont need these values in there anymore otherwise they
                        # would be redundant
                        del argument["name"]
                        del argument["direction"]

            if "name" not in action.keys():
                raise ValueError("Action has not a name assigned.")

            if action["name"] in actions.keys():
                raise ValueError("Action name defined more than ones: " + action["name"])

            # save the action under its name
            actions[action["name"]] = action

            # cleanup, as we have saved the action under its name in the container it would be redundant
            del action["name"]

    def _parseSCPDVariableTypes(self, variableListElement, variableTypes):
        """Internal method to parse the SCPD definitions.

        :param variableListElement: the xml root node of the variable list
        :type variableListElement: xml.etree.ElementTree.Element
        :param dict variableTypes: a container to store the variables
        """

        # iterate through all variables
        for variableElement in variableListElement.getchildren():

            variable = {}

            # iterate through the variable definition
            for inVariableElement in variableElement.getchildren():
                tagName = inVariableElement.tag.lower()

                if tagName.endswith("name"):
                    variable["name"] = inVariableElement.text
                elif tagName.endswith("datatype"):
                    variable["dataType"] = inVariableElement.text
                elif tagName.endswith("defaultvalue"):
                    variable["defaultValue"] = inVariableElement.text

            if "name" not in variable.keys():
                raise ValueError("Variable has no name defined.")

            if "dataType" not in variable.keys():
                raise ValueError("No dataType was defined by variable: " + variable["name"])

            if variable["name"] in variableTypes.keys():
                raise ValueError("Variable has been defined multiple times: " + variable["name"])

            variableTypes[variable["name"]] = variable
