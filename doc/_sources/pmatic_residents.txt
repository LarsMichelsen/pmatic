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

.. automodule:: pmatic.residents
    :members:
    :undoc-members:
