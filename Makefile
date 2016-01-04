VERSION       = 0.1
CHROOT_PATH  ?= $(shell pwd)/chroot
DIST_PATH    ?= $(shell pwd)/dist
CCU_PKG_PATH ?= $(DIST_PATH)/ccu
CCU_HOST     ?= ccu

.PHONY: chroot dist

help:
	@echo
	@echo "Available commands:"
	@echo
	@echo "setup              - Install packages needed for development (at least on debian)"
	@echo "chroot             - Create a debian chroot which is used to get python files for"
	@echo "                     making python available to the CCU later"
	@echo "version            - Set a new version number"
	@echo
	@echo "dist		  - Create all release packages"
	@echo "dist-os            - Create release package for regular systems (Only pmatic)"
	@echo "dist-ccu           - Create addon package for installation on CCU (Python + pmatic)"
	@echo
	@echo "test	          - Run tests incl. coverage analyzing"
	@echo "coverage	          - Report test coverage (short, console)"
	@echo "coverage-html      - Report test coverage (detailed, html)"
	@echo
	@echo "install		  - Install on local system"
	@echo "install-ccu        - Install python and pmatic on the CCU via SSH"
	@echo "install-ccu-python - Install python files from chroot on CCU via SSH"
	@echo "install-ccu-pmatic - Install pmatic files on CCU via SSH"
	@echo
	@echo "clean	          - Cleanup development files (e.g. chroot)"
	@echo

setup:
	apt-get install debootstrap qemu-user-static rsync dialog python-pytest

dist: dist-os dist-ccu

dist-os:
	python setup.py sdist
	@echo "Created dist/pmatic-$(VERSION).tar.gz"

dist-ccu:
	[ ! -d $(DIST_PATH) ] && mkdir $(DIST_PATH) || true
	[ -d $(CCU_PKG_PATH) ] && rm -rf $(CCU_PKG_PATH) || true
	@if ! ls $(CHROOT_PATH)/* >/dev/null 2>&1; then \
	    echo "ERROR: chroot missing. Please run \"make chroot\", then try again." ; \
	    exit 1 ; \
	fi
	mkdir -p $(CCU_PKG_PATH)/python
	cd $(CHROOT_PATH)/usr ; \
	rsync -aRv --no-g \
	    bin/python2.7 \
	    lib/python2.7/site.py \
	    lib/python2.7/os.py \
	    lib/python2.7/traceback.py \
	    lib/python2.7/re.py \
	    lib/python2.7/posixpath.py \
	    lib/python2.7/stat.py \
	    lib/python2.7/genericpath.py \
	    lib/python2.7/warnings.py \
	    lib/python2.7/linecache.py \
	    lib/python2.7/types.py \
	    lib/python2.7/UserDict.py \
	    lib/python2.7/_abcoll.py \
	    lib/python2.7/abc.py \
	    lib/python2.7/_weakrefset.py \
	    lib/python2.7/copy_reg.py \
	    lib/python2.7/sysconfig.py \
	    lib/python2.7/sre_compile.py \
	    lib/python2.7/sre_parse.py \
	    lib/python2.7/sre_constants.py \
	    lib/python2.7/_sysconfigdata.py \
	    lib/python2.7/_sysconfigdata_nd.py \
	    lib/python2.7/subprocess.py \
	    lib/python2.7/pickle.py \
	    lib/python2.7/struct.py \
	    lib/python2.7/json/*.py \
	    lib/python2.7/codecs.py \
	    lib/python2.7/encodings/*.py \
	    lib/python2.7/__future__.py \
	    \
	    lib/python2.7/logging/*.py \
	    lib/python2.7/weakref.py \
	    lib/python2.7/atexit.py \
	    \
	    lib/python2.7/urllib2.py \
	    lib/python2.7/base64.py \
	    lib/python2.7/hashlib.py \
	    lib/python2.7/lib-dynload/_hashlib.so \
	    lib/python2.7/sha.py \
	    lib/python2.7/httplib.py \
	    lib/python2.7/socket.py \
	    lib/python2.7/functools.py \
	    lib/python2.7/urlparse.py \
	    lib/python2.7/collections.py \
	    lib/python2.7/keyword.py \
	    lib/python2.7/heapq.py \
	    lib/python2.7/bisect.py \
	    lib/python2.7/mimetools.py \
	    lib/python2.7/tempfile.py \
	    lib/python2.7/random.py \
	    lib/python2.7/rfc822.py \
	    lib/python2.7/urllib.py \
	    lib/python2.7/string.py \
	    \
	    $(CCU_PKG_PATH)/python
	rsync -aRv --no-g \
	    --exclude=\*.pyc \
	    --exclude=__pycache__ \
	    pmatic examples \
	    $(CCU_PKG_PATH)
	tar -cv -C $(CCU_PKG_PATH) -f $(DIST_PATH)/pmatic-$(VERSION)_ccu.tar .
	tar -rv -C ccu_pkg -f $(DIST_PATH)/pmatic-$(VERSION)_ccu.tar \
	    update_script \
	    python-wrapper \
	    pmatic.init
	gzip -f $(DIST_PATH)/pmatic-$(VERSION)_ccu.tar

chroot:
	[ ! -d $(CHROOT_PATH) ] && mkdir $(CHROOT_PATH) || true
	debootstrap --no-check-gpg --foreign --arch=armel wheezy \
	    $(CHROOT_PATH) http://ftp.debian.org/debian
	cp /usr/bin/qemu-arm-static $(CHROOT_PATH)/usr/bin
	LANG=C chroot $(CHROOT_PATH) /debootstrap/debootstrap --second-stage
	LANG=C chroot $(CHROOT_PATH) apt-get -y --force-yes install python-minimal

test:
	coverage run --source=pmatic setup.py test

coverage:
	coverage report

coverage-html:
	coverage html
	firefox htmlcov/index.html

install:
	python setup.py install

install-ccu: install-ccu-python install-ccu-pmatic

install-ccu-python:
	@echo TODO

install-ccu-pmatic:
	rsync -aRv --no-g \
	    --exclude=\*.pyc \
	    --exclude=__pycache__ \
	    pmatic \
	    root@$(CCU_HOST):/usr/local/etc/config/addons/pmatic/python/usr/lib/python2.7/

version:
	@newversion=$$(dialog --stdout --inputbox "New Version:" 0 0 "$(VERSION)") ; \
        if [ -n "$$newversion" ] ; then \
            $(MAKE) NEW_VERSION=$$newversion setversion ; \
        fi

setversion:
	sed -ri 's/^(VERSION[[:space:]]*= *).*/\1'"$(NEW_VERSION)/" Makefile
	sed -i "s/^VERSION = .*/VERSION = \"$(NEW_VERSION)\"/g" pmatic/__init__.py
	sed -i "s/version='.*',/version='$(NEW_VERSION)',/g" setup.py
	sed -i "s/VERSION=.*,/VERSION=$(NEW_VERSION)/g" ccu_pkg/pmatic.init

clean: clean-chroot clean-dist clean-test

clean-test:
	rm -rf pmatic.egg-info || true
	rm -rf *.egg || true
	rm -rf .coverage htmlcov || true
	rm -rf .cache || true

clean-chroot:
	rm -rf --one-file-system $(CHROOT_PATH)

clean-dist:
	rm -rf build 2>/dev/null || true
	rm -f dist/* 2>/dev/null || true
