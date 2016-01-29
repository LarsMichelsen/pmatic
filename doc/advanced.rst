Advanced things
===============

Build the CCU addon package on your own
---------------------------------------

If you want to create a CCU addon package on your own, follow these steps
on a linux system of your choice. The current Debian or Ubuntu releases are a
good choice, but others should work too:

* download a snapshot of the git repository or clone the repository
* run `make setup chroot dist-ccu`

Now you should have a CCU addon archive at `dist/pmatic-*_ccu.tar.gz`.
You can now upload this file to your CCU to install pmatic on it.
