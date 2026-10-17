#!/usr/bin/env python3
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
import sys
from pathlib import Path

import inkex
from lxml import etree
from subprocess import Popen, PIPE
from shutil import copy2

# Symlinked install: Inkscape's path is the link directory.
_extension_dir = str(Path(__file__).resolve().parent)
if _extension_dir not in sys.path:
    sys.path.insert(0, _extension_dir)

from selection import conversion_actions, id_breaks_actions

# check inkscape version
import importlib
optparse_spec = importlib.util.find_spec("optparse")
if optparse_spec:
    VERSION="1.X"
else:
    VERSION= "0.9"

def convert_objects_to_paths(file, document, ids=None):
    tempfile = os.path.splitext(file)[0] + "-prepare.svg"
    # tempfile is needed here only because we want to force the extension to be .svg
    # so that we can open and close it silently

    if ids:
        for node_id in ids:
            if id_breaks_actions(node_id):
                inkex.errormsg(_(
                    "Cannot convert objects to paths because an id "
                    "contains ';' or a newline."
                ))
                return None

    command = [
        "inkscape",
        file,
        "--actions=" + conversion_actions(ids),
        "-o",
        tempfile,
    ]

    p = Popen(command, shell=False, stdout=PIPE, stderr=PIPE)
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


