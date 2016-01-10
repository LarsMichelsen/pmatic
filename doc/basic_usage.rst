Basic Usage
===========

Please take a look at the scripts below the ``examples`` directory for some
sample scripts. I'll try to add more in the near future.

Just to give you a quick view, here a simple example how to list all shutter
contacts and their current states:

.. code-block:: python

    #!/usr/bin/python

    import pmatic.api
    from pmatic.entities import HMSecSC

    API = pmatic.api.init()

    for device in HMSecSC.get_all(API):
        print("%-20s %6s" % (device.name, device.is_open() and "open" or "closed"))

When I execute this script on my CCU2, I get the following output:

.. code-block:: shell
     
    Kind-Fenster         closed
    Büro-Fenster         closed
    Schlafzimmer-Links   closed
    Bad-Fenster-Rechts   closed
    Bad-Fenster-Links    closed
    Wohnzimmer           closed

Some use cases
--------------

You might use pmatic for different kind of software. Some ideas:

- **Manually triggered one shot scripts**

  The most simple use cases I can imagine is to create small scripts which
  are executed, gather some information, print them or do anything else with
  it and then finish. Of curse these scripts could also trigger something.
  
  An example could be a script which triggers a power switch when you turn on
  your workstation which is then powering on some kind of ambient light.
  
  Take a look at the `example <https://github.com/LaMi-/pmatic/tree/master/examples>`_
  directory for more ideas.

- **Continously running daemons**

  A program which is e.g. starting with the system/CCU, permanently running,
  observing things and performing actions depending on the gathered information.
  
  This daemon could either continously poll the needed information on it's own
  using the APIs pmatic provides or register for specific events happening and
  then perform custom actions.

- **Planned: Scripts executed based on events**

  The event handling is not finished yet, but this will also be a way to use
  pmatic. The complexity is equal to the manually triggered one shot scripts.
  The only difference is that the scripts are registering with pmatic and then
  pmatic is triggering them on it's own when the configured condition to start
  the script is met.
