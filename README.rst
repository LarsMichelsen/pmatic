pmatic
======

.. image:: https://badge.fury.io/py/pmatic.svg
   :target: https://badge.fury.io/py/pmatic
.. image:: https://travis-ci.org/LarsMichelsen/pmatic.svg?branch=master
   :target: https://travis-ci.org/LarsMichelsen/pmatic
.. image:: https://coveralls.io/repos/github/LarsMichelsen/pmatic/badge.svg?branch=master
   :target: https://coveralls.io/github/LarsMichelsen/pmatic?branch=master
.. image:: https://api.codacy.com/project/badge/grade/0b6d7874a5e248a2af685761cccc131c
   :target: https://www.codacy.com/app/lm/pmatic
.. image:: https://landscape.io/github/LarsMichelsen/pmatic/master/landscape.svg?style=flat
   :target: https://landscape.io/github/LarsMichelsen/pmatic/master


Python API for Homematic. Easy to use.

The `pmatic <https://larsmichelsen.github.io/pmatic/>`__ module provides
access to the Homematic CCU which operates as the central unit in
Homematic based home automation setups. You can use pmatic directly on
the CCU or another system having Python installed. With pmatic you can
write your own Python scripts to communicate with your CCU device.

What to do with pmatic?
-----------------------

-  Create even small (one line) scripts to read info or trigger actions.
-  Execute scripts on any linux system or directly on the CCU.
-  Edit scripts in your favorite editor, test on your workstation,
   deploy on another device, for example the CCU, later.
-  Code in a very beginner friendly language: Python.
-  Organize and control your scripts on the CCU using the pmatic manager

Why pmatic?
-----------

Before I built this API I tried to create a small script to *just* check
all my window sensors, record the time they are opened and then alarm me
to close the window if it was open for too long. No problem I thought.
Lesson learned: It is possible. But only while having a huuuuge pain.
The scripting language is crapy, the web GUI editor misses basic things
like syntax highlighting, undo/redo, auto saving and so on which make
programming comfortable. Last but not least the debugging was a pain or
not possible at all.

Should be possible to make this a lot easier.

I found several other middlewares and libraries for accessing the CCU2
APIs, but most of them required to be executed in somehow specific
environments, were not platform independet or implemented in other crapy
programming languages.

I know sure there is still much room for improvement and cleaner APIs,
but for the moment I think even this small API wrapper is an
improvement.

So how does it work?
--------------------

pmatic has been implemented in Python. What? Python is not available on
the CCU2, do I need to run it remotely on a separate device now? Yes,
you can. But it is also possible to use it on the CCU2 by installing a
python interpreter with the necessary modules on the device. We'll get
back to it later.

So you have the option to run your pmatic scripts remotely and on the
CCU2. The code stays the same. This means you can develop your scripts
on your workstation, test and debug it using a remote connection to your
CCU2.

You can use all the API methods provided by the CCU2. The data is parsed
and available as python lists or dicts. You can then process the data in
your Python code and use the editor of your choice, use all possible
debugging and profiling features you can imagine with Python.

It's so much fun :-).

Even if you write pmatic in Python, you can also execute custom ReGa
(Homematic Script) through pmatic and also process the output of these
scripts, if you like.

The pmatic manager provides you with a web GUI on your CCU which you can
use to manage (upload, delete, test) your pmatic scripts with. You can
also create scheduling plans in which situations your scripts should be
executed automatically. This can currently be on manager startup, based
on time or based on device events reported by the CCU. Take a look at
the documentation for screenshots and more details.

Requirements
------------

Pmatic is currently not expecting any special Python modules. pmatic is
supported with Python 2.7, 3.4 and newer. Older versions of Python are
not supported.

The pmatic package can be installed and used on the Homematic CCU2 device
without any other requirements. The package ships whole Python installation
and pmatic with it. Please note that pmatic will not work on the CCU1,
because the ressources on the CCU1 are too limited.

There are some which are already use pmatic on Windows systems which
have a Python interpreter installed. But I did not test it and I am
pretty sure there are some changes needed to make it completely work. At
least the pmatic Manager will not work without some changes.

At least the basic functionality of Pmatic has also been tested on OS X
using Python 2.7 and 3.4 from MacPorts. But as for Windows the pmatic
Manager has not been tested on OS X yet.

I am always open to support more platforms. So if one likes to add
support for more, please let me know.

Installation
------------

Take a look at the `installation
documentation <https://larsmichelsen.github.io/pmatic/doc/install.html>`__.

Documentation
-------------

The current
`documentation <https://larsmichelsen.github.io/pmatic/doc/index.html>`__
can be found on the official web site of pmatic.

Usage
-----

You can find several usage examples in the ``examples``. I'll try to add
more in the near future. Some more examples can be found in the
`documentation <https://larsmichelsen.github.io/pmatic/doc/basic_usage.html>`__.

Just a short example:

::

    #!/usr/bin/python

    import pmatic
    ccu = pmatic.CCU()

    for device in ccu.devices.query(device_type="HM-Sec-SC"):
        print("%-20s %6s" % (device.name, device.is_open and "open" or "closed"))

What is planned?
----------------

Please take a look at the issue tracker and the TODO file.

What really is needed is specific support for the different Homematic
devices. I added some specific classes for devices I have to the
``pmatic/devices.py`` but have not added properties and methods to
reflect their individual features. And there are also a lot of devices I
don't own. It would be really helpful if you could help out adding more
devices to pmatic.

This will make it a lot easier to use pmatic. Because, for example
calling ``device.is_battery_low`` is a lot more comfortable than digging
into the details of a device and find out you have to call
``self.channels[4].values["FAULT_REPORTING"].formated() == "LOWBAT"``.

So please help adding more devices!

Changes
-------

Please take a look at the `changelog
<https://github.com/LarsMichelsen/pmatic/blob/master/CHANGELOG.rst>`__
for a detailed list of changes.

Reporting Bugs, Feature Requests
--------------------------------

Please use the issue tracker on the `pmatic GitHub
page <https://github.com/LarsMichelsen/pmatic>`__.

Licensing
---------

Copyright © 2016 Lars Michelsen lm@larsmichelsen.com. All rights
reserved.

All outcome of the project is licensed under the terms of the GNU GPL
v2. Take a look at the LICENSE file for details.
