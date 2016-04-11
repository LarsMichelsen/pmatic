Specific Devices
================

Pmatic supports all kind of devices which are provided by the CCU. Those unspecific devices
are instances of :class:`pmatic.entities.Device`. Those device values can be read and
written with generic methods and properties. You can e.g. retrieve the current temperature
measured by a HM-CC-RT-DN device as floating point number using
``device.channels[4].values["ACTUAL_TEMPERATURE"].value``. To get this right, you need to
know several things: 

  * You need to know that the channel 4 of the device is the ``CLIMATECONTROL_RT_TRANSCEIVER`` channel.
  * You need to know that the current temperature is available via the paramater ``ACTUAL_TEMPERATURE``.

I think thats problematic. You need to dig into documents and API descriptions of the manufacturers
which should really not be neccessary.

So there is the concept of specific device objects in pmatic. To stick with the example above,
there is the :class:`pmatic.entities.HMCCRTDN` which is automatically used for HM-CC-RT-DN devices.
When working with such a device, you have access to the property ``device.temperature`` which gives
you the same value as the code above. Now that should be clear. We need specific devices!

HMCCRTDN - HM-CC-RT-DN (Funk-Heizkörperthermostat)
--------------------------------------------------

.. autoclass:: pmatic.entities.HMCCRTDN
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

HMSecSC - HM-Sec-SC (Funk-Tür-/ Fensterkontakt)
-----------------------------------------------

.. autoclass:: pmatic.entities.HMSecSC
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

HMESPMSw1Pl - HM-ES-PMSw1-Pl (Funk-Schaltaktor mit Leistungsmessung)
--------------------------------------------------------------------

.. autoclass:: pmatic.entities.HMESPMSw1Pl
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

HMPBI4FM - HM-PBI-4-FM (Funk-Tasterschnittstelle 4-fach)
--------------------------------------------------------

.. autoclass:: pmatic.entities.HMPBI4FM
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

HM-WDS10-TH-O (Funk-Temperatur-/Luftfeuchtesensor OTH)
--------------------------------------------------------

.. autoclass:: pmatic.entities.HM_WDS10_TH_O
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

The Channels
------------

Each device is organized in several independent channels which all have individual features.
This chapter describes all specific channels currently implemented in pmatic. Unknown channels
are represented by the generic :class:`pmatic.entities.Channel` class.

ChannelMaintenance
^^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelMaintenance
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name,name,id

ChannelShutterContact
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelShutterContact
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelSwitch
^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelSwitch
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelKey
^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelKey
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelVirtualKey
^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelVirtualKey
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelPowermeter
^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelPowermeter
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelConditionPower
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelConditionPower
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelConditionCurrent
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelConditionCurrent
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelConditionVoltage
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelConditionVoltage
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelConditionFrequency
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelConditionFrequency
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelWeather
^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelWeather
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelClimaVentDrive
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelClimaVentDrive
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelClimaRegulator
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelClimaRegulator
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name

ChannelClimaRTTransceiver
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.entities.ChannelClimaRTTransceiver
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: type_name
