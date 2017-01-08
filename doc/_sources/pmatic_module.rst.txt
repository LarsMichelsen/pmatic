The pmatic Module
=================

CCU - The Central Object
------------------------

.. automodule:: pmatic
    :members:
    :undoc-members:
    :exclude-members: bidcos_interfaces,interfaces,signal_strengths

CCUDevices - Top Level Collection of Devices
--------------------------------------------

.. autoclass:: pmatic.ccu.CCUDevices
    :show-inheritance:
    :members:
    :undoc-members:
    :special-members:
    :exclude-members: __init__,__module__,initialized,add_from_low_level_dict,already_initialized_devices

Devices - Collections of Devices
--------------------------------

.. autoclass:: pmatic.entities.Devices
    :members:
    :undoc-members:
    :special-members:
    :exclude-members: __init__,__module__,__dict__,__weakref__

Device - Device connected with the CCU
--------------------------------------

.. autoclass:: pmatic.entities.Device
    :members:
    :undoc-members:
    :exclude-members: get_devices

Channel - Manages values
------------------------

.. autoclass:: pmatic.entities.Channel
    :members:
    :undoc-members:
    :exclude-members: set_logic_attributes

CCURooms - Top Level Collection of Rooms
----------------------------------------

.. autoclass:: pmatic.ccu.CCURooms
    :show-inheritance:
    :members:
    :undoc-members:
    :special-members:
    :exclude-members: __init__,__module__,__dict__,__weakref__

Rooms - Collections of Rooms
----------------------------

.. autoclass:: pmatic.entities.Rooms
    :members:
    :undoc-members:
    :special-members:
    :exclude-members: __init__,__module__,__dict__,__weakref__

Room - A Configured Room
------------------------

.. autoclass:: pmatic.entities.Room
    :members:
    :undoc-members:

EventListener - Listen for CCU Events
-------------------------------------

.. autoclass:: pmatic.events.EventListener
    :members:
    :undoc-members:

Parameters
----------

Parameter
^^^^^^^^^

.. autoclass:: pmatic.params.Parameter
    :show-inheritance:
    :members:
    :undoc-members:
    :exclude-members: set_from_api
    :special-members: __str__,__bytes__,__unicode__


ParameterSTRING
^^^^^^^^^^^^^^^

.. autoclass:: pmatic.params.ParameterSTRING
    :show-inheritance:
    :members:
    :undoc-members:


ParameterNUMERIC
^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.params.ParameterNUMERIC
    :show-inheritance:
    :members:
    :undoc-members:
    :special-members: __eq__,__ne__,__gt__,__lt__,__ge__,__le__

ParameterINTEGER
^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.params.ParameterINTEGER
    :show-inheritance:
    :members:
    :undoc-members:


ParameterFLOAT
^^^^^^^^^^^^^^

.. autoclass:: pmatic.params.ParameterFLOAT
    :show-inheritance:
    :members:
    :undoc-members:


ParameterENUM
^^^^^^^^^^^^^

.. autoclass:: pmatic.params.ParameterENUM
    :show-inheritance:
    :members:
    :undoc-members:


ParameterBOOL
^^^^^^^^^^^^^

.. autoclass:: pmatic.params.ParameterBOOL
    :show-inheritance:
    :members:
    :undoc-members:


ParameterACTION
^^^^^^^^^^^^^^^

.. autoclass:: pmatic.params.ParameterACTION
    :show-inheritance:
    :members:
    :undoc-members:


ParameterControlMode
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pmatic.params.ParameterControlMode
    :show-inheritance:
    :members:
    :undoc-members:
