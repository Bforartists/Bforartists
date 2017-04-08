#!/usr/bin/env python3
"""
This script takes 2-3 args: [--browse] <Doxyfile> <sourcefile>

Where Doxyfile is a path relative to source root,
and the sourcefile as an absolute path.

--browse will open the resulting docs in a web browser.
"""
import sys
import os
import subprocess
import tempfile


def find_gitroot(filepath_reference):
    path = filepath_reference
    path_prev = ""
    while not os.path.exists(os.path.join(path, ".git")) and path != path_prev:
        path_prev = path
        path = os.path.dirname(path)
    return path

doxyfile, sourcefile = sys.argv[-2:]

doxyfile = os.path.join(find_gitroot(sourcefile), doxyfile)
os.chdir(os.path.dirname(doxyfile))

tempfile = tempfile.NamedTemporaryFile(mode='w+b')
doxyfile_tmp = tempfile.name
tempfile.write(open(doxyfile, "r+b").read())
tempfile.write(b'\n\n')
tempfile.write(b'INPUT=' + os.fsencode(sourcefile) + b'\n')
tempfile.flush()

subprocess.call(("doxygen", doxyfile_tmp))
del tempfile

# Maybe handy, but also annoying?
if "--browse" in sys.argv:
    import webbrowser
    webbrowser.open("html/files.html")
