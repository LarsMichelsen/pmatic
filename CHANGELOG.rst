The pmatic Changelog
====================

Unreleased (Use snapshot builds to get these changes)
-----------------------------------------------------
* HM-CC-RT-DN: Fixed low battery detection via ``device.is_battery_low``
* HM-CC-RT-DN: Added specific attributes/methods: ``device.temperature``,
  ``device.set_temperature``, ``device.is_off``, ``device.turn_off()``,
  ``device.control_mode``, ``device.battery_state``, ``device.boost_duration``,
  ``device.set_temperature_comfort()``, ``device.set_temperature_lowering()``,
  ``device.valve_state``
* Manager: The manager can now be used with Python 3 (testing in progress)
* Manager: Schedules that rely on devices can now be edited even when the
  manager is currently not connected with the CCU.
* Windows: Made CCU detection platform independent
* Windows: Made setup.py more platform independent
* Better linking from addon page to the manager page

Incompatible (possible manual changes needed):

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
