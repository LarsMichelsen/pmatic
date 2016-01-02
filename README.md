# pmatic - A simple API to to the Homematic CCU2

[![Build Status](https://travis-ci.org/LaMi-/pmatic.svg?branch=master)](https://travis-ci.org/LaMi-/pmatic)
[![Coverage Status](https://coveralls.io/repos/LaMi-/pmatic/badge.svg?branch=master&service=github)](https://coveralls.io/github/LaMi-/pmatic?branch=master)

pmatic is a python library to provide access to the Homematic CCU2. You
can execute pmatic directly on the CCU2 or another system having Python
installed. With pmatic you can write your own Python scripts to communicate
with your CCU2 devices.

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

pmatic is currently not expecting any special Python modules. pmatic
is supported with Python 2.7 and newer. Older versions of Python are not
supported.

## Installation

### Installation on the CCU2

The current, not ideal way, is to use the Makefile shipped with the pmatic
source. You need to first enable SSH access to your CCU2. Then you need to
run the following command to install Python and pmatic on your device:

```
CCU_HOST=ccu make install-ccu
```

If your ccu is not reachable using the host name *ccu*, you can simply replace
it in the command above with the host address of your CCU2.

The installation procedure assumes you have an SD card inserted and formated
and installs Python and pmatic to `/media/sd-mmcblk0/pmatic` on your CCU2.
The python interpreter is then available at
`/media/sd-mmcblk0/pmatic/usr/bin/python2.7`. You can use it to execute your
Python scripts now.

I saw there is some way to create CCU addon packages which might be the best
way to deploy pmatic on the CCU, but I did not get into this yet.

### Installation on your workstation

The installation should be straight forward. First download pmatic by either
cloning from the Git or download a release archive, unpack it and change to
the extracted directory `pmatic-*`. Then execute:

```
python setup.py install
```

After installation you can confirm pmatic has been installed by executing

```
python -c 'import pmatic'
```

When the command completes silently (without `ImportError` exception) the
installation was successful.


I developed and tested pmatic on a Debian 8 system with Python 2.7.9, but
pmatic should work on other platforms meeting the requirements listed above.

Please let me know or send me a pull request if there are compatibility
issues on a platform you would expect pmatic to work.

## Usage

Please take a look at the scripts below the `examples` directory for some
sample scripts. I'll try to add more in the near future. Just to give you
a quick view, here a simple example how to list all shutter contacts and 
their current states on the CCU2:

```
import pmatic.api
from pmatic.entities import HMSecSC

API = pmatic.api.init()

for device in HMSecSC.get_all(API):
    print device.name, device.formated_value()
```

## Reporting Bugs, Feature Requests

Please use the issue tracker on the [pmatic GitHub page](https://github.com/LaMi-/pmatic).

## Licensing

Copyright (C) 2016 Lars Michelsen <lm@larsmichelsen.com>

All outcome of the project is licensed under the terms of the GNU GPL v2.
Take a look at the LICENSE file for details.
