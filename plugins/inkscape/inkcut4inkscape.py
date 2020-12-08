#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inkcut, Plot HPGL directly from Inkscape.
   inkcut4inkscape.py

   Copyright 2018 The Inkcut Team

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
   MA 02110-1301, USA.
"""
import os
import inkex
from lxml import etree
from subprocess import Popen, PIPE
from shutil import copy2
from distutils.spawn import find_executable

# check inkscape version
import importlib
optparse_spec = importlib.util.find_spec("optparse")
if optparse_spec:
    VERSION="1.X"
else:
    VERSION= "0.9"

def contains_text(nodes):
    for node in nodes:
        tag = node.tag[node.tag.rfind("}")+1:]
        if tag == 'text':
            return True
    return False

def convert_objects_to_paths(file, document):
    tempfile = os.path.splitext(file)[0] + "-prepare.svg"
    # tempfile is needed here only because we want to force the extension to be .svg
    # so that we can open and close it silently

    command = 'inkscape ' + file + ' --actions="select-all;object-unlink-clones;object-to-path" -o ' + tempfile

    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    (out, err) = p.communicate()

    if p.returncode != 0:
        inkex.errormsg(_("Failed to convert objects to paths. Continued without converting."))
        inkex.errormsg(out)
        inkex.errormsg(err)
        return document.getroot()
    else:
        if VERSION == "1.X":
            return etree.parse(tempfile).getroot()
        else:
            return inkex.etree.parse(tempfile).getroot()


