# pmatic - A simple to use API to the Homematic CCU2

[![Build Status](https://travis-ci.org/LaMi-/pmatic.svg?branch=master)](https://travis-ci.org/LaMi-/pmatic)
[![Coverage Status](https://coveralls.io/repos/LaMi-/pmatic/badge.svg?branch=master&service=github)](https://coveralls.io/github/LaMi-/pmatic?branch=master)

pmatic is a python library to provide access to the Homematic CCU2. You
can execute pmatic directly on the CCU2 or another system having Python
installed. With pmatic you can write your own Python scripts to communicate
with your CCU2 devices.

## What to do with pmatic?

* Create even small scripts to read info or trigger actions.
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

### Installation on the CCU2

pmatic can be packed as CCU addon package. Currently you can download the
snapshot addon from [here](http://lami-.github.io/pmatic/pmatic-snapshot_ccu.tar.gz).
It is a snapshot package which is automatically built from the latest
git version available. So please note that this is not as stable as a
released version would be. But feel free to try and test it. Let me know
if you experience any issues with it.

[Download the file](http://lami-.github.io/pmatic/pmatic-snapshot_ccu.tar.gz)
to your workstation and upload this file to your CCU using the regular addon
upload form to install pmatic on it.

Now you can connect to your CCU via SSH and run this command to confirm
pmatic has been installed correctly:

```
python -c 'import pmatic'
```

When the command completes silently (without `ImportError` exception) the
installation was successful.

The installation has been finished. You can now execute your own
python and pmatic scripts on your CCU. For some examples you can change
to `/etc/config/addons/pmatic/examples` and have a look at the source or
just try them.

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

Copyright (C) 2016 Lars Michelsen <lm@larsmichelsen.com>

All outcome of the project is licensed under the terms of the GNU GPL v2.
Take a look at the LICENSE file for details.
