The pmatic Changelog
====================

Unreleased (Use snapshot builds to get these changes)
-----------------------------------------------------

General
```````

* Improved low level API error handling when trying to use calls which need arguments
  but using positional arguments instead of named arguments
* FIX: Fixed quoting of arguments passed to CCU local low level API
* FIX: Fixed encoding of arguments passed to CCU local low level API

Manager
```````

* FIX: Fixed manual execution of scripts via the "execute scripts" dialog
* FIX: Schedules executed on startup were not shown as triggered and running in GUI
* FIX: Fixed visualization of "keep alive" scripts current state when aborted via GUI
* FIX: Fixed file descriptor inheritance to "external executed" scripts
  (could block manager port during restar)

Version 0.4 (2016-07-14)
------------------------

General
```````

* FIX: Fixed possible endless recursion when listening for device updates
* New helper function for calculating the sun position (``utils.sun_position()``)
  Thanks to Rolf Hempel for implementation!
* New helper function for calculating the dew point (``utils.dew_point()``)
  Thanks to Rolf Hempel for implementation!

Devices
```````

* Added specific device object HM-WDS40-TH-I-2
* Added specific device object HM-Sen-LI-O
* Added specific device object HM-LC-Sw1-Pl-DN-R1
* Added specific device object HM-LC-Bl1PBU-FM

Thanks to Rolf Hempel for adding all of them!

Manager
```````

* Implemented transaction IDs to prevent duplicate execution of actions
  like form submits, script executions or deletion of things
* Improved performance during processing of web pages
* Added yet unfunctional schedule execution based on device events
* Added schedule execution based on device events for devices of a specific type
* FIX: Fixed exception in event processing of non readable values

Version 0.3 (2016-04-19)
------------------------

General
```````

* Added missing install requirements to setup.py: requests, SimpleTR64
* The local/remote detection (``utils.is_ccu()``) is now detecting "local" mode on LXCCU
* Improved error handling of fetched values with the current CCU firmware (2.17.15)
  This firmware fails with error code 501 instead of 601 in case of values that can not
  be fetched for some reason.
* CCU Package: Precompiling all Python files to ``*.pyc`` now for faster initial loading

Devices
```````

* Added specific device object for HM-WDS10-TH-O
* Added specific device object for HM-Sec-SCo
* HM-TC-IT-WM-W-EU: Added missing specific channel ``ChannelWeatherTransmit``

Manager
```````

* Resident and schedule states are now persisted between manager restarts. Please note
  that the current default state directory is ``/var/lib/pmatic`` which is not reboot
  persistant on the CCU. So the resident and schedule states will be reset on reboot.
* Schedule/Resident pages can now only be accessed after setting the manager password.
* Scripts started with "Execute Scripts" can now be run in inline mode
* Schedules: Showing next execution time for timed schedules
* FIX: Fixed custom config via command line not setting new defaults for the argument parsing
  (e.g. ccu_enabled could not be changed to ``False`` using a config file provided by (``-o``).
* FIX: Fixed startup error when connection to CCU is not possible
* FIX: Fixed error during saving of manager config/state files when base directory not
  exists. Trying to create the directory now.
* FIX: Fixed multiple execution of single schedule when multiple timed conditions match
  at the same time
* FIX: Fixed problem in enumeration of schedules/residents after deleting one object

Documentation
`````````````

* Added missing documentation of Parameter classes

Incompatible (possible manual changes needed)
`````````````````````````````````````````````

* Cleanup: Renamed all specific device classes to use underscores
  (e.g. HMPBI4FM to HM_PBI_4_FM)


Version 0.2 (2016-04-07)
------------------------

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
* FIX: Fixed wrong type for boolean parameter default value

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
* Maintenance channel: Fixed broken ``maintenance_state`` property

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
