"""
TR 64 specific actions
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2015 by Benjamin Pannier.
:license: Apache 2.0, see LICENSE for more details.

"""
from .lan import Lan, HostDetails, EthernetInfo, EthernetStatistic
from .system import System, SystemInfo, TimeInfo
from .wan import Wan, WanLinkInfo, WanLinkProperties, ConnectionInfo, ADSLInfo
from .wifi import Wifi, WifiDeviceInfo, WifiBasicInfo
from .fritz import Fritz
