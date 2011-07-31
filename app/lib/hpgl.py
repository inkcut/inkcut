#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: hpgl.py
# Author: Copyright 2011 Jairus Martin <frmdstryr@gmail.com>
# Date: 28 July 2011
# Version: 0.1
#
# License:
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import logging
log = logging.getLogger(__name__)

from plugin import Plugin
from graphic import Graphic

class HPGLPlugin(Plugin):
    def __init__(self):
        super(Plugin,self).__init__()
        self.name = "HPGL"
        self.mode = "export"
        self.filetypes = [".hpgl"]

    def run(self):
        """ Converts an SVG into HPGL. """
        super(Plugin,self).run()

        # See http://www.w3.org/TR/SVG/coords.html#Units and
        # http://en.wikipedia.org/wiki/HPGL
        HPGL_SCALE = 1016/90.0

        # Set initial HPGL commands
        hpgl = ['IN','SP1']
        hpgl.extend(self.commands['send_before'])

        if self.device['cutting_force'][1]:
            hpgl.append('FS%d'%self.device['cutting_force'][0])

        if self.device['cutting_speed'][1]:
            hpgl.append('VS%d'%self.device['cutting_speed'][0])

        # Read the input SVG into a Graphic to provide easy manipulation.
        g = Graphic(etree.parse(self.input))
        g.set_rotation(self.device['axis_rotation'])
        g.set_scale(self.device['axis_scale'][0]*HPGL_SCALE,self.device['axis_scale'][1]*HPGL_SCALE)
        g.set_position(self.device['axis_translate'][0],self.device['axis_translate'][1])

        # Create the HPGL data
        paths = g.get_polyline()

        # Apply device specific settings
        self.apply_cutting_overlap(paths,self.device['cutting_overlap'))
        self.apply_cutting_blade_offset(paths,self.device['cutting_blade_offset'))

        data = []
        for path in paths:
            x,y = path.pop(0)[1]
            data.append('PU%i,%i'%(round(x),round(y)))
            for line in path:
                x,y = line[1]
                data.append('PD%i,%i'%(round(x),round(y)))

        hpgl.extend(data)
        hpgl.extend(self.commands['send_after'])

        # Not friendly for large files!
        return hpgl


def parse(hgpl): # hpgl to polyline # todo, full parsing...
    if type(hpgl) == str:
        hpgl = hpgl.split(';')
    assert type(hpgl)==list, 'hpgl must be a list or string'
    err = []
    poly = []
    pen = ['PU','PD','PR','PD']
    z = True # True == pen is up
    i = 0
    while i < len(hpgl):
        cmd = hpgl[i][:2]
        if cmd == 'PU':
            z = True
        elif cmd == 'PD':
            z = False

        if cmd in pen and len(hpgl[i])>2:
            if z:
                c = 'M'
            else:
                c = 'L'
            poly.append([c,map(int,hpgl[i][2:].split(','))])
        else:
            err.append['unsupported command %s'%(cmd)]
            # screw it...
        i+=1
    if len(err):
        return err
    else: # error free
        return poly

def format(poly): # polyline to hpgl
    hpgl = []
    line = poly.pop(0) # first is moveto/pen up
    hpgl.append('PU%d,%d'%(map(round,line[1])))
    for line in poly:
        hpgl.append('PD%d,%d'%(map(round,line[1])))
    return hpgl
