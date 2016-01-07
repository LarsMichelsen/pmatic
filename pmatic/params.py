#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - A simple API to to the Homematic CCU2
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

# Relevant docs:
# - http://www.eq-3.de/Downloads/PDFs/Dokumentation_und_Tutorials/HM_Script_Teil_4_Datenpunkte_1_503.pdf
# - http://www.eq-3.de/Downloads/PDFs/Dokumentation_und_Tutorials/HM_XmlRpc_V1_502__2_.pdf

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:
    # Is recommended for Python 3.x but fails on 2.7, but is not mandatory
    from builtins import object
except ImportError:
    pass

import pmatic.entities
from pmatic import utils
from pmatic.exceptions import PMException, PMActionFailed


class Parameter(object):
    datatype = "string"

    transform_attributes = {
        # mask: 1=Read, 2=Write, 4=Event
        'OPERATIONS' : int,
        'TAB_ORDER'  : int,
        # mask: 
        # 0x01 : Visible-Flag. Dieser Parameter sollte für de
        # n Endanwender sichtbar sein. 
        # 0x02 : Internal-Flag. Dieser Parameter wird nur int
        # ern verwendet. 
        # 0x04 : Transform-Flag. Änderungen dieses Parameters
        #  ändern das Verhalten des 
        #  entsprechenden Kanals völlig. Darf nur geändert wer
        #  den, wenn keine Verknüpfungen 
        #  am entsprechenden Kanal vorhanden sind. 
        #  0x08 : Service-Flag. Dieser Parameter soll als Serv
        #  icemeldung behandelt werden. Als 
        #  Datentyp für Servicemeldungen sind nur Boolean und 
        #  Integer zulässig. Bei 0 bzw. false liegt dabei keine
        #  Meldung vor, ansonsten liegt eine Meldung vor. 
        #  0x10 : Sticky-Flag. Nur bei Servicemeldungen. Servi
        #  cemeldung setzt sich nicht selbst 
        #  zurück, sondern muss von der Oberfläche zurückgeset
        #  zt werden. 
        'FLAGS'      : int,
    }


    def __init__(self, channel, spec, api_value):
        assert isinstance(channel, pmatic.entities.Channel), "channel is not a Channel: %r" % channel
        assert type(spec) == dict, "spec is not a dictionary: %r" % spec
        self.channel = channel
        self._init_attributes(spec)

        if api_value == None:
            self._value = self.default
        else:
            self._value = self._from_api_value(api_value)


    def _init_attributes(self, spec):
        for key, val in spec.items():
            # Optionally convert values using the given transform functions
            # for the specific object type
            trans_func = self.transform_attributes.get(key)
            if trans_func:
                val = trans_func(val)

            setattr(self, key.lower(), val)


    def _from_api_value(self, value):
        """Transforms the value coming from the API to the pmatic internal format."""
        return value


    def _to_api_value(self, value):
        """Transforms the pmatic internal value to API format."""
        return value


    def _validate(self, value):
        return True

    @property
    def readable(self):
        """Whether or not this value can be read."""
        return self.operations & 1 == 1

    @property
    def writable(self):
        """Whether or not this value can be set."""
        return self.operations & 2 == 2

    @property
    def supports_events(self):
        """Whether or not this value supports events."""
        return self.operations & 4 == 4

    @property
    def title(self):
        return self.name.title().replace("_", " ")


    @property
    def value(self):
        if not self.readable:
            raise PMException("The value can not be read.")
        return self._value


    @property
    def is_visible_to_user(self):
        """Whether or not this parameter should be visible to the end-user."""
        return self.flags & 1 == 1


    @property
    def is_internal(self):
        """Whether or not this parameter is an internal flag."""
        return self.flags & 2 == 2


    @property
    def is_transformer(self):
        """Whether or not modifying this parameter changes behaviour of this channel.

        Can only be changed when no links are configured for this channel."""
        return self.flags & 4 == 4


    @property
    def is_service(self):
        """Whether or not a maintenance message is available."""
        return self.flags & 8 == 8


    @property
    def is_service_sticky(self):
        """Whether or not there is a sticky maintenance message."""
        return self.flags & 16 == 16


    @value.setter
    def value(self, value):
        if not self.writable:
            raise PMException("The value can not be changed.")
        self._validate(value)

        result = self.channel.API.interface_set_value(
            interface="BidCos-RF",
            address=self.channel.address,
            valueKey=self.id,
            type=self.datatype,
            value=self._to_api_value(value)
        )
        if not result:
            raise PMActionFailed("Failed to set the value in CCU.")

        self._value = value


    def set(self, value):
        try:
            self.value = value
            return True
        except PMActionFailed:
            return False


    def set_to_default(self):
        self.value = self.default


    def formated(self, value_format="%s"):
        if self.unit:
            if self.unit == "%":
                return (value_format+"%%") % self.value
            else:
                return (value_format+" %s") % (self.value, self.unit)
        return value_format % self.value


    def __str__(self):
        """Returns the formated value. Data type differs depending on Python version.

        In Python 2 it returns an UTF-8 encoded string.
        In Python 3+ it returns a unicode string of type str.
        """
        if utils.is_py2():
            return self.formated().encode("utf-8")
        else:
            return self.formated()


    def __bytes__(self):
        """Returns the formated value UTF-8 encoded. Only relevant for Python 3."""
        return self.formated().encode("utf-8")


    def __unicode__(self):
        """Returns the formated value as unicode string. Only relevant for Python 2."""
        return self.formated()


class ParameterINTEGER(Parameter):
    datatype = "integer"

    transform_attributes = dict(Parameter.transform_attributes,
        DEFAULT=int,
        MAX=int,
        MIN=int
    )

    def _from_api_value(self, value):
        return int(value)


    def _to_api_value(self, value):
        return "%d" % value


    def _validate(self, value):
        if type(value) != int:
            raise PMException("Invalid type. You need to provide an integer value.")

        if value > self.max:
            raise PMException("Invalid value (Exceeds maximum of %d)" % self.max)

        if value < self.min:
            raise PMException("Invalid value (Exceeds minimum of %d)" % self.min)

        return True


    def formated(self):
        return super(ParameterINTEGER, self).formated("%d")



class ParameterSTRING(Parameter):
    pass



class ParameterFLOAT(Parameter):
    datatype = "float"
    transform_attributes = dict(Parameter.transform_attributes,
        DEFAULT=float,
        MAX=float,
        MIN=float
    )


    def _from_api_value(self, value):
        return float(value)


    def _to_api_value(self, value):
        """Transforms the float value to an API value.

        The precision is set to 2 digits. Hope this is ok."""
        return "%0.2f" % value


    def _validate(self, value):
        if type(value) not in (float, int):
            raise PMException("Invalid type. You need to provide a float value.")

        if value > self.max:
            raise PMException("Invalid value (Exceeds maximum of %0.2f)" % self.max)

        if value < self.min:
            raise PMException("Invalid value (Exceeds minimum of %0.2f)" % self.min)

        return True


    def formated(self):
        return super(ParameterFLOAT, self).formated("%0.2f")


class ParameterBOOL(Parameter):
    datatype = "boolean"

    def _from_api_value(self, value):
        return value == "1"


    def _to_api_value(self, value):
        return value and "true" or "false"


    def _validate(self, value):
        if type(value) != bool:
            raise PMException("Invalid type. You need to provide a bool value.")

        return True


# 'control': u'NONE', 'operations': 5, 'name': u'ERROR', 'min': 0, 'default': 0, 'max': 4, '_value': 0, 'tab_order': 1, 'value_list': u'NO_ERROR VALVE_DRIVE_BLOCKED VALVE_DRIVE_LOOSE ADJUSTING_RANGE_TO_SMALL LOWBAT', 'flags': 9, 'unit': u'', 'type': u'ENUM', 'id': u'ERROR', 'channel': <pmatic.entities.ChannelClimaVentDrive object at 0x7fb7574b6750>}
class ParameterENUM(ParameterINTEGER):
    transform_attributes = dict(ParameterINTEGER.transform_attributes,
        VALUE_LIST=lambda v: v.split(" "),
    )

    @property
    def possible_values(self):
        """ Returns a python list of possible values.

        The indexes in this list represent the digit to be used as value."""
        return self.value_list


    def formated(self):
        return self.value_list[self.value]


class ParameterACTION(ParameterBOOL):
    pass
