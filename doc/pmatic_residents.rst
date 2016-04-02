Manage your Residents
=====================

You can manage your residents either in your own scripts by using the :class:`pmatic.residents`
class or within the manager by configuring your residents using the GUI and then access the
residents configured attributes like email address, mobile number or pushover tokens from your
own pmatic scripts. Another interesting topic is the presence detection of your residents, take
a look at that chapter below.

.. _presence_detection:

Presence detection with pmatic
------------------------------

An important task in home automation is to detect whether or not someone is at home or not.
I personally use the presence information to route notifications to the different residents,
for example to close a window when it is open for too long.

Currently pmatic comes with one presence plugin which uses the fritz!Box connected devices
list (Home Network) to detect whether or not a device (person) is present. It explicitly does
not use a direct ping to any device because it is not possible to detect e.g. the iPhone in
the LAN by using ping by default. But the list of the fritz!Box works like a charm for any
mobile phone I tested.

To make it even more comfortable the pmatic Manager has a dedicated GUI to configure your
users and devices. Within the manager you can even trigger scripts when a user arrives or
leaves.

Example: Logging presence every 5 minutes
````````````````````````````````````````````

To make it comfortable the pmatic Manager has a dedicated GUI to configure your
users and devices. Within the manager you can even trigger scripts when a user arrives or
leaves.

When executing scripts from the manager using inline scripts, you can access the residents
configured via the manager by using the residents instance of the globally available CCU
object. You don't need to care for updating the data on your own or loading the residents.
And you even don't need to configure the fritz!Box credentials within the script as they
are already configured within the manager.

You can simply start with the logic you like to implement. If you add a schedule that is
being executed every 5 minutes, you get a log file in the path `/tmp/presence-test.log`
which contains one entry for each resident which contains it's name and presence status.

.. code-block:: python

    #!/usr/bin/python
    import pmatic, time
    ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

    for resident in ccu.residents.residents:
        open("/tmp/presence-test.log", "a").write(time.strftime("%Y-%m-%d %H:%M:%S") + " " +
            resident.name + " " + (resident.present and "is at home\n" or "is not at home\n"))


However, it even possible to make your script being executed upon user arrival or departure
using the "on resident presence" condition. This lets you get rid of the timed polling and
you'll have a log which only contains the changes in presence.


Example: Accessing resident properties
````````````````````````````````````````````

Once you have configured your residents, you can use their attributes like phone number,
pushover token or email address in your scripts. Please take a look at this example:

.. code-block:: python

    #!/usr/bin/python
    import pmatic
    ccu = pmatic.CCU(address="http://192.168.1.26", credentials=("Admin", "EPIC-SECRET-PW"))

    lars = ccu.residents.get_by_name("Lars")
    if lars is None:
        print("You don't have a resident \"Lars\". Feeling sorry.")
        sys.exit(1)

    print("Mail           : %s" % lars.email)
    print("Phone Phone    : %s" % lars.phone)
    print("Pushover Token : %s" % lars.pushover_token)

    # And now? Maybe send a notification using pmatic.notify?
    # from pmatic.notify import Pushover
    # Pushover.send("Hallo Lars :-)", user_token=lars.pushover_token, api_token="...")

This script will output something like this when you have a resident called Lars:

.. code-block:: shell

    Mail           : lm@larsmichelsen.com
    Mobile Phone   : +4912312312312
    Pushover Token : KLAH:AWHFlawfkawjd;kawjd;lajw


The pmatic.residents module
------------------------------

.. automodule:: pmatic.residents
    :show-inheritance:
    :members:
    :undoc-members:
