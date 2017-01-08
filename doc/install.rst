Installation
============

pmatic can either be installed and used on any Linux system of your choice having
Python installed or directly on the Homematic CCU. Later might be useful if you
want to run your scripts when all your other devices aren't running.

Installation on the CCU2
------------------------

You have two options to download pmatic. To have a stable version, you should
download a released version from the `GitHub releases page of pmatic <https://github.com/LarsMichelsen/pmatic/releases>`_.
To get the CCU addon you need to download the file named like ``pmatic-*_ccu.tar.gz``.

If you feel adventurous and like to test the newest changes, you can download a snapshot
CCU addon package from `here <https://larsmichelsen.github.io/pmatic/pmatic-snapshot_ccu.tar.gz>`_.
It is a snapshot package which is automatically built from the latest
git version available. So please note that this is not as stable as a
released version would be. But feel free to try and test it. Let me know
if you experience any issues with it. Once there is a better version ready
I'll change these lines.

Once you downloaded the version of your choice, open up the Web Interface of the CCU in 
your browser and upload this file to your CCU using the regular addon upload form
(In German: "Einstellungen / Systemsteuerung / Zusatzsoftware") to install pmatic on it.

After the CCU has been restarted, pmatic should have been installed. You can now use
the pmatic Manager, which can be opened from the addon menu you used before to install
pmatic. Open this dialog again. You should see an entry for the pmatic addon and a link
to the pmatic manager in the right column. If you click on it, the pmatic manager will
be opened. Here you can see a list of example scripts which you can try to execute now.

If you like to stick to the command line instead, you can connect to your CCU via SSH
and run this command to confirm pmatic has been installed correctly:

.. code-block:: shell

  python -c 'import pmatic'

When the command completes silently (without ``ImportError`` exception) the
installation was successful.

The installation has been finished. You can now execute your own
python and pmatic scripts on your CCU. For some examples you can change
to ``/etc/config/addons/pmatic/scripts/examples`` and have a look at the source or
just try them.

Your own scripts should be placed in the directory ``/etc/config/addons/pmatic/scripts``
or any directory below. This makes the scripts accessible through command line and
through the pmatic manager.

As I only have a CCU2, not a CCU, I don't know whether or not pmatic is
working on the CCU too. But I hope so. Please let me know if it is working
or not.

Installation on your workstation
--------------------------------

The easiest way is to use ``pip`` for installation. Simply execute

.. code-block:: shell

  pip install --upgrade pmatic

If this does not work for you for some reason, you can install pmatic manually. This should
also be straight forward. First download pmatic by either downloading a released version from
the `PyPI pmatic page <https://pypi.python.org/pypi/pmatic>`_ or the
`GitHub releases page of pmatic <https://github.com/LarsMichelsen/pmatic/releases>`_, the
`current git snapshot <https://larsmichelsen.github.io/pmatic/pmatic-snapshot.tar.gz>`_ or
by cloning the `Git repository <https://github.com/LarsMichelsen/pmatic>`_.
Then unpack it and change to the extracted directory ``pmatic-*``. Then execute:

.. code-block:: shell

  python setup.py install

After installation you can confirm pmatic has been installed by executing

.. code-block:: shell

    python -c 'import pmatic'

When the command completes silently (without ``ImportError`` exception) the
installation was successful.


I developed and tested pmatic on a Debian 8 system with Python 2.7.9, but
pmatic should work on other platforms meeting the pmatic requirements. It is also
tested with all current Python 3 versions.

Please let me know or send me a pull request on GitHub if there are compatibility
issues on a platform you would expect pmatic to work.
