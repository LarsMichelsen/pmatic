Installation
============

pmatic can either be installed and used on any Linux system of your choice having
Python installed or directly on the Homematic CCU. Later might be useful if you
want to run your scripts when all your other devices aren't running.

Installation on the CCU2
------------------------

You can download the snapshot addon from `here <https://larsmichelsen.github.io/pmatic/pmatic-snapshot_ccu.tar.gz>`_.
It is a snapshot package which is automatically built from the latest
git version available. So please note that this is not as stable as a
released version would be. But feel free to try and test it. Let me know
if you experience any issues with it. Once there is a better version ready
I'll change these lines.

`Download the file <https://larsmichelsen.github.io/pmatic/pmatic-snapshot_ccu.tar.gz>`_
to your workstation and upload this file to your CCU using the regular addon
upload form to install pmatic on it.

Now you can connect to your CCU via SSH and run this command to confirm
pmatic has been installed correctly:

.. code-block:: shell

  python -c 'import pmatic'

When the command completes silently (without ``ImportError`` exception) the
installation was successful.

The installation has been finished. You can now execute your own
python and pmatic scripts on your CCU. For some examples you can change
to ``/etc/config/addons/pmatic/examples`` and have a look at the source or
just try them.

As I only have a CCU2, not a CCU, I don't know whether or not pmatic is
working on the CCU too. But I hope so. Please let me know if it is working
or not.

Installation on your workstation
--------------------------------

The installation should be straight forward. First download pmatic by either
cloning from the Git or download a release archive, unpack it and change to
the extracted directory ``pmatic-*``. Then execute:

.. code-block:: shell

  python setup.py install

After installation you can confirm pmatic has been installed by executing

.. code-block:: shell

    python -c 'import pmatic'

When the command completes silently (without ``ImportError`` exception) the
installation was successful.


I developed and tested pmatic on a Debian 8 system with Python 2.7.9, but
pmatic should work on other platforms meeting the requirements listed above.

Please let me know or send me a pull request on GitHub if there are compatibility
issues on a platform you would expect pmatic to work.
