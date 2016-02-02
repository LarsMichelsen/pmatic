The pmatic Module
-----------------

CCU - The Central Object
========================

.. automodule:: pmatic
    :members:
    :undoc-members:
    :exclude-members: bidcos_interfaces,interfaces,signal_strengths

CCUDevices - Top Level Collection of Devices
============================================

.. autoclass:: pmatic.ccu.CCUDevices
    :show-inheritance:
    :members:
    :undoc-members:
    :special-members:
    :exclude-members: __init__,__module__

Devices - Collections of Devices
================================

.. autoclass:: pmatic.entities.Devices
    :members:
    :undoc-members:
    :special-members:
    :exclude-members: __init__,__module__

Device - Device connected with the CCU
======================================

.. autoclass:: pmatic.entities.Device
    :members:
    :undoc-members:
    :exclude-members: get_devices

Channel - Manages values
========================

.. autoclass:: pmatic.entities.Channel
    :members:
    :undoc-members:

CCURooms - Top Level Collection of Rooms
========================================

.. autoclass:: pmatic.ccu.CCURooms
    :show-inheritance:
    :members:
    :undoc-members:
    :special-members:
    :exclude-members: __init__,__module__

Rooms - Collections of Rooms
=============================

.. autoclass:: pmatic.entities.Rooms
    :members:
    :undoc-members:
    :special-members:
    :exclude-members: __init__,__module__

Room - A Configured Room
========================

.. autoclass:: pmatic.entities.Room
    :members:
    :undoc-members:

EventListener - Listen for CCU Events
=====================================

.. autoclass:: pmatic.events.EventListener
    :members:
    :undoc-members:
