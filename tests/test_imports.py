#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - Python API for Homematic. Easy to use.
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
import glob
import shutil
import pytest
import subprocess

requires_snakefood = pytest.mark.skipif(
                        os.system("python -c \"import snakefood\" >/dev/null 2>&1") >> 8 != 0,
                                reason="requires snakefood")

path_patterns = [
    "pmatic-manager"
] + glob.glob(os.path.join("pmatic", "*.py")) \
  + glob.glob(os.path.join("tests", "*.py")) \
  + glob.glob(os.path.join("examples", "*.py")) \
  + glob.glob(os.path.join("examples", "*", "*.py"))

@requires_snakefood
def test_invalid_imports():
    p = subprocess.Popen("python -c \"from snakefood.checker import main "
                         "; main()\" %s" % " ".join(path_patterns),
                         cwd=repo_dir(),
                         shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout = p.communicate()[0]

    assert stdout == b""


# Puts all python modules / files mentioned in the module lists to a temporary
# directory which is then later used to check whether or not all imported modules
# are available using these modules.
def populate_tmp_dir(target_path):
    if "TRAVIS" in os.environ:
        src_dirs = [
            glob.glob("/home/travis/virtualenv/python2.7.*")[0],
            glob.glob("/opt/python/2.7.*")[0],
        ]
    elif sys.platform == "win32":
        src_dirs = [sys.prefix]
    else:
        src_dirs = ["/usr"]

    #print("Base source directories: %r" % src_dirs)
    #print("Target path: %s" % target_path)

    for list_file, optional in [ ("python-modules.list",          False),
                                 ("python-modules-travis.list",   True),
                                 ("python-modules-optional.list", True) ]:
        list_path = os.path.join(repo_dir(), "ccu_pkg", list_file)
        for l in open(list_path):
            line = l.strip()
            if not line or line[0] == "#":
                continue

            matched_files = []
            for src_dir in src_dirs:
                for matched in glob.glob(os.path.join(src_dir, line)):
                    if os.path.isfile(matched):
                        rel_path = os.path.dirname(matched[len(src_dir)+1:])
                        matched_files.append((matched, rel_path))

            if not matched_files and not optional:
                raise Exception("Did not find a file for %s from %s." % (line, list_file))

            for file_path, rel_path in matched_files:
                target_file_path = os.path.join(target_path, rel_path, os.path.basename(file_path))

                if not os.path.exists(os.path.dirname(target_file_path)):
                    os.makedirs(os.path.dirname(target_file_path))

                #print("%s => %s" % (file_path, target_file_path))
                shutil.copy(file_path, target_file_path)


def find_imports():
    p = subprocess.Popen("python -c \"from snakefood.list import main ; main()\" "
                         "-u %s" % " ".join([ p for p in path_patterns
                                              if not p.startswith("tests/") ] ),
                         cwd=repo_dir(),
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
            "queue",
            "io.",
            "http.",
            "urllib.error",
            "urllib.parse",
            "urllib.request",
            "builtins",
            "xmlrpc.server",
            # Skip aliases resulting from "import logging as _logging"
            "_logging",
            # This module is not available in travis tests
            # (for unknown reasons, but it is ok. No need to verify this)
            "_struct",
        ]

        skip = False
        for prefix in ignore_prefixes:
            if line.startswith(prefix):
                skip = True
        if skip:
            continue

        imports.append(line)
    return imports


def repo_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# This tests aim is to verify that all imports are available on the
# CCU and there we have only Python 2.7. So don't care about other versions.
@pytest.mark.skipif(sys.version_info >= (3,0),
                    reason="requires python2.7")
@pytest.mark.skipif(sys.platform == "win32",
                    reason="did not want to port it to windows, "
                          +"testing on linux is enough")
@requires_snakefood
def test_ccu_imports(tmpdir):
    path = "%s" % tmpdir
    populate_tmp_dir(path)

    imports = find_imports()
    assert len(imports) > 30

    p = subprocess.Popen([path + "/bin/python2.7"], cwd=repo_dir(),
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
