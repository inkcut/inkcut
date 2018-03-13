#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inkcut, Plot HPGL directly from Inkscape.
   extension.py

   Copyright 2010 Jairus Martin <frmdstryr@gmail.com>

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
import inkex
inkex.localize()
import subprocess

from subprocess import Popen, PIPE
from shutil import copy2
from distutils.spawn import find_executable

DEBUG = False

try:
    from subprocess import DEVNULL # py3k
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')


class InkscapeInkcutPlugin(inkex.Effect):
    def contains_text(self):
        nodes = self.selected.values()
        for node in nodes:
            tag = node.tag[node.tag.rfind("}")+1:]
            if tag == 'text':
                return True
        return False

    def convertObjectsToPaths(self, file, document):
        tempfile = inkex.os.path.splitext(file)[0] + "-prepare.svg"
        # tempfile is needed here only because we want to force the extension to be .svg
        # so that we can open and close it silently
        copy2(file, tempfile)

        command = 'inkscape --verb=EditSelectAllInAllLayers --verb=EditUnlinkClone --verb=ObjectToPath --verb=FileSave --verb=FileQuit ' + tempfile

        if find_executable('xvfb-run'):
            command = 'xvfb-run ' + command

        p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        (out, err) = p.communicate()

        if p.returncode != 0:
            inkex.errormsg(_("Failed to convert objects to paths. Continued without converting."))
            inkex.errormsg(out)
            inkex.errormsg(err)
            return document.getroot()
        else:
            return inkex.etree.parse(tempfile).getroot()

    def effect(self):
        """ Like cut but requires no selection and does no validation for
        text nodes.
        """
        nodes = self.selected
        if not len(nodes):
            inkex.errormsg("There were no paths were selected.")
            return

        document = self.document
        if self.contains_text():
            document = self.convertObjectsToPaths(self.args[-1], self.document)

        #: If running from source
        if DEBUG:
            python = '~/inkcut/venv/bin/python'
            inkcut = '~/inkcut/main.py'
            cmd = [python, inkcut]
        else:
            cmd = ['inkcut']

        cmd += ['open', '-',
               '--nodes']+[str(k) for k in nodes.keys()]
        p = subprocess.Popen(cmd,
                             stdin=subprocess.PIPE,
                             stdout=DEVNULL,
                             stderr=subprocess.STDOUT,
                             close_fds=True)
        p.stdin.write(inkex.etree.tostring(document))
        p.stdin.close()

# Create effect instance and apply it.
effect = InkscapeInkcutPlugin()
effect.affect()
