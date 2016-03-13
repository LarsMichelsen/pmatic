#!/usr/bin/env python
import pandoc

doc = pandoc.Document()
doc.markdown = open('README.md').read()

f = open('README.rst','w+')
for l in doc.rst.split("\n"):
    if not l or (not l[0] == '|' and not l[-1] == '|'):
        f.write(l+"\n")
f.close()
