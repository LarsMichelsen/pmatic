# pmatic - A simple to use API to the Homematic CCU2

[![Build Status](https://travis-ci.org/LaMi-/pmatic.svg?branch=master)](https://travis-ci.org/LaMi-/pmatic)
[![Coverage Status](https://coveralls.io/repos/LaMi-/pmatic/badge.svg?branch=master&service=github)](https://coveralls.io/github/LaMi-/pmatic?branch=master)

The pmatic module provides access to the Homematic CCU which operates as
the central unit in Homematic based home automation setips.. You can use
pmatic directly on the CCU2 or another system having Python installed.
With pmatic you can write your own Python scripts to communicate with
your CCU device.

## What to do with pmatic?

* Create even small (one line) scripts to read info or trigger actions.
* Execute scripts on any linux system or directly on the CCU.
* Edit scripts in your favorite editor, test on your workstation,
  deploy on another device, for example the CCU, later.
* Code in a very beginner friendly language: Python.

## Why pmatic?

Before I built this API I tried to create a small script to *just* check
all my window sensors, record the time they are opened and then alarm
me to close the window if it was open for too long. No problem I thought.
Lesson learned: It is possible. But only while having a huuuuge pain.
The scripting language is crapy, the web GUI editor misses basic things
like syntax highlighting, undo/redo, auto saving and so on which make
programming comfortable. Last but not least the debugging was a pain
or not possible at all.

Should be possible to make this a lot easier.

I found several other middlewares and libraries for accessing the CCU2
APIs, but most of them required to be executed in somehow specific
environments, were not platform independet or implemented in other crapy
programming languages.

I know sure there is still much room for improvement and cleaner APIs,
but for the moment I think even this small API wrapper is an improvement.

## So how does it work?

pmatic has been implemented in Python. What? Python is not available on
the CCU2, do I need to run it remotely on a separate device now? Yes,
you can. But it is also possible to use it on the CCU2 by installing
a python interpreter with the necessary modules on the device. We'll
get back to it later.

So you have the option to run your pmatic scripts remotely and on the
CCU2. The code stays the same. This means you can develop your scripts
on your workstation, test and debug it using a remote connection to
your CCU2.

You can use all the API methods provided by the CCU2. The data is parsed
and available as python lists or dicts. You can then process the data
in your Python code and use the editor of your choice, use all possible
debugging and profiling features you can imagine with Python.

It's so much fun :-).

Even if you write pmatic in Python, you can also execute custom ReGa
(Homematic Script) through pmatic and also process the output of these
scripts, if you like.

## Requirements

pmatic is currently not expecting any special Python modules. pmatic is
supported with Python 2.7, 3.4 and newer. Older versions of Python are not
supported.

Potentially pmatic could even be used on Windows systems which have a
Python interpreter installed. But I did not test it and I am pretty sure
there are some changes needed to make it work. But maybe someone wants
to make this work. Should not be too much work.

## Installation

Take a look at the [installation documentation](http://lami-.github.io/pmatic/doc/install.html).

## Documentation

The current [documentation](http://lami-.github.io/pmatic/doc/index.html)
can be found on the official web site of pmatic.

## Usage

You can find several usage examples in the `examples`. I'll try to add more
in the near future. Some more examples can be found in the
[documentation](http://lami-.github.io/pmatic/doc/basic_usage.html).

Just a short example:

```
#!/usr/bin/python

import pmatic
ccu = pmatic.CCU()

for device in ccu.devices.get(device_type="HM-Sec-SC"):
    print("%-20s %6s" % (device.name, device.is_open() and "open" or "closed"))
```

### Some use cases

You might use pmatic for different kind of software. Some ideas:

#### Manually triggered one shot scripts

The most simple use cases I can imagine is to create small scripts which
are executed, gather some information, print them or do anything else with
it and then finish. Of curse these scripts could also trigger something.

An example could be a script which triggers a power switch when you turn on
your workstation which is then powering on some kind of ambient light.

Take a look at the `example` directory for more ideas.

#### Continously running daemons

A program which is e.g. starting with the system/CCU, permanently running,
observing things and performing actions depending on the gathered information.

This daemon could either continously poll the needed information on it's own
using the APIs pmatic provides or register for specific events happening and
then perform custom actions.

#### Planned: Scripts executed based on events

The event handling is not finished yet, but this will also be a way to use
pmatic. The complexity is equal to the manually triggered one shot scripts.
The only difference is that the scripts are registering with pmatic and then
pmatic is triggering them on it's own when the configured condition to start
the script is met.

## Advanced topic: Build the CCU addon package on your own

If you want to create a CCU addon package on your own, follow these steps
on a linux host:

* download a snapshot of the git repository or clone the repository
* run `make setup chroot dist-ccu`

Now you should have a CCU addon archive at `dist/pmatic-*_ccu.tar.gz`.
You can now upload this file to your CCU to install pmatic on it.

## What is planned?

Please take a look at the issue tracker and the TODO file.

## Reporting Bugs, Feature Requests

Please use the issue tracker on the [pmatic GitHub page](https://github.com/LaMi-/pmatic).

## Licensing

Copyright © 2016 Lars Michelsen <lm@larsmichelsen.com>. All rights reserved.

All outcome of the project is licensed under the terms of the GNU GPL v2.
Take a look at the LICENSE file for details.
