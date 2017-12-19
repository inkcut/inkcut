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
import inkex
inkex.localize()
import subprocess


class InkscapeInkcutPlugin(inkex.Effect):

    def effect(self):
        """ Like cut but requires no selection and does no validation for 
        text nodes. 
        """
        p = subprocess.Popen(['inkcut', 'open', '-'],
                             stdin=subprocess.PIPE,
                             stdout=None,
                             stderr=subprocess.STDOUT,
                             close_fds=True)
        p.stdin.write(inkex.etree.tostring(self.document))
        p.stdin.close()

# Create effect instance and apply it.
effect = InkscapeInkcutPlugin()
effect.affect()
