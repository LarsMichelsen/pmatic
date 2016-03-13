#!/usr/bin/env python
import pandoc
import os

doc = pandoc.Document()
doc.markdown = open('README.md').read()

f = open('README.rst','w+')
for l in doc.rst.split("\n"):
    if not l.startswith("|Build Status"):
        f.write(l+"\n")
f.close()
