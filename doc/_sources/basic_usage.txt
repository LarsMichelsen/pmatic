Basic Usage
===========

Please take a look at the scripts below the ``examples`` directory for some
sample scripts. I'll try to add more in the near future.

List shutter contact states
---------------------------

Just to give you a quick view, here a simple example how to list all shutter
contacts and their current states:

.. code-block:: python

    #!/usr/bin/python
    import pmatic

    for device in pmatic.CCU().devices.query(device_type="HM-Sec-SC"):
        print("%-20s %6s" % (device.name, device.is_open and "open" or "closed"))

When I execute this script on my CCU2, I get the following output:

.. code-block:: shell

    Kind-Fenster         closed
    Büro-Fenster         closed
    Schlafzimmer-Links   closed
    Bad-Fenster-Rechts   closed
    Bad-Fenster-Links    closed
    Wohnzimmer           closed

The same script can now be executed from another system, e.g. a linux workstation,
just by adding the address and credentials to access the CCU.

.. code-block:: python
   :emphasize-lines: 5

    #!/usr/bin/python
    import pmatic
    ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

    for device in ccu.devices.query(device_type="HM-Sec-SC"):
        print("%-20s %6s" % (device.name, device.is_open and "open" or "closed"))

Please note: I moved the CCU object definition to a separate line for readability.

If you execute the exact same script directly on the CCU you may notice that it works
even if you leave the credentials in the script. So your scrips developed on your
workstation can be moved to the CCU and executed on it without change.

List devices on low battery
---------------------------

Besides the current states of devices, you can also query for maintenance information like
whether or not devices are currently reachable or have a low battery.

.. code-block:: python

    #!/usr/bin/python
    import pmatic
    ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

    print("Low battery: ")
    for device in ccu.devices:
        if device.is_battery_low:
            print("  %s" % device.name)
    else:
        print("  All battery powered devices are fine.")

Trigger actions
---------------

Or do you want to simulate key presses of your buttons (e.g. HM-PBI-4-FM)?

.. code-block:: python

    #!/usr/bin/python
    import pmatic
    ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

    for device in ccu.devices.query(device_name=u"Büro-Schalter"):
        if device.button(0).press_short():
            print("done.")
        else:
            print("failed!")

This scripts searches for the device having the name ``Büro-Schalter`` which is a HM-PBI-4-FM
device. This device has 4 buttons which can be pressed for a short and long time. The script
is simulating a short press of button 0 (the first button) and checks whether or not the
command succeeded.

Print temperature updates
-------------------------

This example simply prints out all temperatures reported by the devices of type HM-CC-TC,
HM-WDS10-TH-O and HM-CC-RT-DN.

This script is executed until terminated by the user (e.g. via CTRL+C). It listens for
incoming events and prints a message to the user once the a temperature update is received.

This detection is using the events sent by the CCU. So the state updates are printed nearly
instantly.

.. code-block:: python

    #!/usr/bin/python
    import pmatic
    ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

    devices = ccu.devices.query(device_type=["HM-CC-TC", "HM-WDS10-TH-O", "HM-CC-RT-DN"])

    # This function is executed on each state update
    def print_summary_state(param):
        print("%s %s" % (param.channel.device.name, param.channel.summary_state))

    devices.on_value_updated(print_summary_state)

    if not devices:
        print("Found no devices. Terminating.")
    else:
        print("Waiting for changes...")

        ccu.events.init()
        ccu.events.wait()
        ccu.events.close()


List Rooms with their devices
-----------------------------

You can even get the devices grouped by the rooms which they are associated with. Accessing
the rooms is similar to the devices. See an example below which prints out all devices
grouped by the rooms.

.. code-block:: python

    #!/usr/bin/python
    import pmatic
    ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

    for room in ccu.rooms:
        print(room.name)
        for device in room.devices:
            print(" ", device.name)

This script produces an output like this:

.. code-block:: shell

    Wohnzimmer
      Wohnzimmer-Licht
      Wohnzimmer-Schalter
      Wohnzimmer-Tür
    Schlafzimmer
      Schlafzimmer-Links-Heizung
    Büro
      Büro-Fenster
      Büro-Lampe
      Büro-Schalter

Some use cases
--------------

You might use pmatic for different kind of software. Some ideas:

- **Manually triggered one shot scripts**

  The most simple use cases I can imagine is to create small scripts which
  are executed, gather some information, print them or do anything else with
  it and then finish. Of curse these scripts could also trigger something.

  An example could be a script which triggers a power switch when you turn on
  your workstation which is then powering on some kind of ambient light.

  Take a look at the `example <https://github.com/LarsMichelsen/pmatic/tree/master/examples>`_
  directory for more ideas.

- **Continously running daemons**

  A program which is e.g. starting with the system/CCU, permanently running,
  observing things and performing actions depending on the gathered information.

  This daemon could either continously poll the needed information on it's own
  using the APIs pmatic provides or register for specific events happening and
  then perform custom actions.

- **Scripts executed based on events**

  You can use the pmatic manager to deal with the CCUs events and create schedules
  which are triggered when events for specific devices are received.

  It is also possible to do the event handling on your own. Take a look at the
  "Print temperature updates" example above.
