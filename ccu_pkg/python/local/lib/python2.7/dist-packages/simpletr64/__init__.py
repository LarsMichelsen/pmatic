"""
Simple TR64-UPnP library
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2016 by Benjamin Pannier.
:license: Apache 2.0, see LICENSE for more details.

"""
from .devicetr64 import DeviceTR64
from .discover import Discover, DiscoveryResponse
from .actions.lan import Lan, HostDetails, EthernetInfo, EthernetStatistic
from .actions.system import System, SystemInfo, TimeInfo
from .actions.wan import Wan, WanLinkInfo, WanLinkProperties, ConnectionInfo, ADSLInfo
from .actions.wifi import Wifi, WifiDeviceInfo, WifiBasicInfo

__title__ = 'simpletr64'
__version__ = '1.0.6'
__author__ = 'Benjamin Pannier'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2016 Benjamin Pannier'
