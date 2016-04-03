The pmatic Changelog
====================

Unreleased (Use snapshot builds to get these changes)
-----------------------------------------------------

General
```````

* Added new resident management module ``pmatic.residents`` which can be used to
  manage residents and their attributes. An important feature of this module 
  is to detect the presence of your residents and make your scripts do different
  things depending on the presence of them. Take a look at the docs for details.
* Windows: Made CCU detection platform independent
* Windows: Made setup.py more platform independent
* OS X: Made setup.py and tests work on OS X. Pmatic should be usable on this platform too.
* CCU: Better linking from addon page to the manager page
* FIX: Fixed API call ``room_get_all()`` failing when meta names like "${roomKitchen}" are used.
* FIX: Improved generic error handling for values which are reported to be readable
  but can currently not be read
* FIX: Fixed possible wrong encoding when using ``Pushover.send()``

Devices
```````

* HM-CC-RT-DN: Fixed low battery detection via ``device.is_battery_low``
* HM-CC-RT-DN: Added specific attributes/methods:

  * ``device.temperature``
  * ``device.set_temperature``
  * ``device.is_off``
  * ``device.turn_off()``
  * ``device.control_mode``
  * ``device.battery_state``
  * ``device.boost_duration``
  * ``device.set_temperature_comfort()``
  * ``device.set_temperature_lowering()``
  * ``device.valve_state``

* HM-TC-IT-WM-W-EU: Fixed "JSONRPCError: TCL error (601)" when trying to get
  the summary state of this device

Manager
```````

* The manager can now be used with Python 3 (testing in progress)
* Schedules that rely on devices can now be edited even when the
  manager is currently not connected with the CCU.
* Improved handling of deleted scripts in schedules
* Changing the log level is now applied instantly
* Added "status" target to init script
* Added time interval to "based on time" condition
* Improved error handling of inline executed scripts
* Fixed exception when doing API calls (caused by wrong locking of local TCL API)
* Fixed "restart" target of init script

Incompatible (possible manual changes needed)
`````````````````````````````````````````````

* ``Device.maintenance`` now provides access to the ``ChannelMaintenance``
  object instead of only the maintenance values. If you want to access the
  maintenance values as before, you need to use ``Device.maintenance.values```
* HM-PBI-4-FM: Changed access to switches from ``device.button(0)`` to
  a hopefully clearer ``device.switch1``, ``device.switch2``, ...
* ``Room.ids()`` has been moved to ``Room.ids`` and is now returing the list
  of room ids sorted.

Version 0.1 (2016-03-13)
------------------------

* Initial testing release.
