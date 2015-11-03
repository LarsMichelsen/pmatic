CHROOT_PATH ?= $(shell pwd)/chroot
CCU_HOST    ?= ccu

.PHONY: chroot

help:
	@echo
	@echo "Available commands:"
	@echo
	@echo "setup              - Install packages needed for development (at least on debian)"
	@echo "chroot             - Create a debian chroot which is used to get python files for"
	@echo "                     making python available to the CCU later"
	@echo "install-ccu        - Install python and pmatic on the CCU via SSH"
	@echo "install-ccu-python - Install python files from chroot on CCU via SSH"
	@echo "install-ccu-pmatic - Install pmatic files on CCU via SSH"
	@echo
	@echo "clean	          - Cleanup development files (e.g. chroot)"
	@echo

setup:
	apt-get install debootstrap qemu-user-static rsync

chroot:
	[ ! -d $(CHROOT_PATH) ] && mkdir $(CHROOT_PATH) || true
	debootstrap --no-check-gpg --foreign --arch=armel wheezy \
	    $(CHROOT_PATH) http://ftp.debian.org/debian
	cp /usr/bin/qemu-arm-static $(CHROOT_PATH)/usr/bin
	LANG=C chroot $(CHROOT_PATH) /debootstrap/debootstrap --second-stage
	LANG=C chroot $(CHROOT_PATH) apt-get -y install python-minimal

install-ccu: install-ccu-python install-ccu-pmatic

install-ccu-python:
	@if ! ls $(CHROOT_PATH)/* >/dev/null 2>&1; then \
	    echo "ERROR: chroot missing. Please run \"make chroot\", then try again." ; \
	    exit 1 ; \
	fi
	cd $(CHROOT_PATH) ; \
	rsync -aRv --no-g \
	    usr/bin/python2.7 \
	    usr/lib/python2.7/site.py \
	    usr/lib/python2.7/os.py \
	    usr/lib/python2.7/traceback.py \
	    usr/lib/python2.7/re.py \
	    usr/lib/python2.7/posixpath.py \
	    usr/lib/python2.7/stat.py \
	    usr/lib/python2.7/genericpath.py \
	    usr/lib/python2.7/warnings.py \
	    usr/lib/python2.7/linecache.py \
	    usr/lib/python2.7/types.py \
	    usr/lib/python2.7/UserDict.py \
	    usr/lib/python2.7/_abcoll.py \
	    usr/lib/python2.7/abc.py \
	    usr/lib/python2.7/_weakrefset.py \
	    usr/lib/python2.7/copy_reg.py \
	    usr/lib/python2.7/sysconfig.py \
	    usr/lib/python2.7/sre_compile.py \
	    usr/lib/python2.7/sre_parse.py \
	    usr/lib/python2.7/sre_constants.py \
	    usr/lib/python2.7/_sysconfigdata.py \
	    usr/lib/python2.7/_sysconfigdata_nd.py \
	    usr/lib/python2.7/subprocess.py \
	    usr/lib/python2.7/pickle.py \
	    usr/lib/python2.7/struct.py \
	    usr/lib/python2.7/json/*.py \
	    usr/lib/python2.7/codecs.py \
	    usr/lib/python2.7/encodings/*.py \
	    root@$(CCU_HOST):/media/sd-mmcblk0/pmatic

install-ccu-pmatic:
	rsync -aRv --no-g \
	    test.py pmatic \
	    root@$(CCU_HOST):/media/sd-mmcblk0/pmatic

clean: clean-chroot

clean-chroot:
	rm -rf --one-file-system $(CHROOT_PATH)
