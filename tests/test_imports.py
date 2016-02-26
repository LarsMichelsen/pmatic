#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - A simple API to to the Homematic CCU2
# Copyright (C) 2016 Lars Michelsen <lm@larsmichelsen.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import pytest
import tempfile
import subprocess

requires_snakefood = pytest.mark.skipif(
                        os.system("which sfood-checker >/dev/null") >> 8 != 0,
                                reason="requires snakefood")

@requires_snakefood
def test_invalid_imports():
    p = subprocess.Popen("sfood-checker pmatic-manager pmatic/*.py "
                         "tests/*.py examples/*.py examples/*/*.py",
                         shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout = p.communicate()[0]

    assert stdout == b""


def populate_tmp_dir(path, repo_dir):
    os.system("TARGET_DIR=%s make -C %s copy-ccu-python-modules-for-test" %
                                        (path, repo_dir))


def find_imports():
    p = subprocess.Popen("sfood-imports -u pmatic-manager pmatic/*.py "
                         "examples/*.py examples/*/*.py",
                         shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    assert stderr == b""

    imports = []
    for l in stdout.split("\n"):
        line = l.strip()
        if not line:
            continue

        ignore_prefixes = [
            "pmatic",
            ".pmatic",
            # Skip known "python 3 only" imports
            "io.",
            "http.",
            "urllib.error",
            "urllib.parse",
            "urllib.request",
            "builtins",
            "xmlrpc.server",
            # Skip aliases resulting from "import logging as _logging"
            "_logging",
        ]

        skip = False
        for prefix in ignore_prefixes:
            if line.startswith(prefix):
                skip = True
        if skip:
            continue

        imports.append(line)
    return imports


# This tests aim is to verify that all imports are available on the
# CCU and there we have only Python 2.7. So don't care about other versions.
@pytest.mark.skipif(sys.version_info >= (3,0),
                    reason="requires python2.7")
@requires_snakefood
def test_ccu_imports():
    path = tempfile.mkdtemp(prefix="tmp_test_ccu_modules_")
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    populate_tmp_dir(path, repo_dir)

    imports = find_imports()
    assert len(imports) > 30

    p = subprocess.Popen([path + "/bin/python2.7"], cwd=repo_dir,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    test_code = []
    for m in imports:
        if "." in m:
            module, thing = m.rsplit(".", 1)
            test_code.append("from %s import %s" % (module, thing))
        else:
            test_code.append("import %s" % m)

    #print("\n".join(test_code))

    stdout, stderr = p.communicate("\n".join(test_code))

    assert stdout == b""
    assert stderr == b""
    assert p.returncode == 0
