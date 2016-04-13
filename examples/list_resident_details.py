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

# Pmatic has a concept of persons and the presence of persons. For each
# person multiple devices can be configured which can then be used to
# detect the presence of a person. It is implemented as plugin mechanism
# which can be extended easily. For the start there is a plugin to control
# a persons availability by a device which is connected withe a fritz!Box
# in your local network.

import pmatic, sys
ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

# Now load some resident data. When executed from the manager as inline script, you
# will automatically have the residents configured in the manager loaded. Otherwise
# you have to use ccu.residents.load(config_file="...") or do something like this:
#ccu.residents.from_config({
#    "residents": [
#        {
#            "id"             : 0,
#            "name"           : "Lars",
#            "email"          : "lm@larsmichelsen.com",
#            "mobile"         : "+4912312312312",
#            "pushover_token" : "KLAH:AWHFlawfkawjd;kawjd;lajw",
#            "devices": [
#                {
#                    "type_name": "fritz_box_host",
#                    "mac": "30:10:E6:10:D4:B2",
#                },
#            ]
#        }
#    ],
#})

lars = ccu.residents.get_by_name("Lars")
if lars is None:
    print("You don't have a resident \"Lars\". Feeling sorry.")
    sys.exit(1)

print("Mail           : %s" % lars.email)
print("Mobile Phone   : %s" % lars.mobile)
print("Pushover Token : %s" % lars.pushover_token)

# And now? Maybe send a notification using pmatic.notify?
# from pmatic.notify import Pushover
# Pushover.send("Hallo Lars :-)", user_token=lars.pushover_token, api_token="...")

