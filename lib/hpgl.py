#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: hpgl.py
# Author: Copyright 2011 Jairus Martin <frmdstryr@gmail.com>
# Date: 6 August 2011
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
from graphic import Graphic,SVG
from lxml import etree

# See http://www.w3.org/TR/SVG/coords.html#Units and
# http://en.wikipedia.org/wiki/HPGL
HPGL_SCALE = 1016/90.0

class Export(Plugin):
    def __init__(self):
        super(Plugin,self).__init__()
        self.name = "HPGL"
        self.mode = "export"
        self.filetypes = ["hpgl"]

    def run(self):
        """ Converts an SVG into HPGL. """

        # Set initial HPGL commands
        hpgl = ['IN','SP1']
        hpgl.extend(self.commands['send_before'])

        if self.device['cutting_force'][1]:
            hpgl.append('FS%d'%self.device['cutting_force'][0])

        if self.device['cutting_speed'][1]:
            hpgl.append('VS%d'%self.device['cutting_speed'][0])

        # Read the input SVG into a Graphic to provide easy manipulation.
        g = Graphic(self.input)
        g.set_rotation(self.device['axis_rotation'])
        g.set_mirror_x(True) # The coordinate systems are flipped in HPGL from SVG
        g.set_scale(self.device['axis_scale'][0]*HPGL_SCALE,self.device['axis_scale'][1]*HPGL_SCALE)
        g.set_position(self.device['axis_translate'][0],self.device['axis_translate'][1])
        g.set_smoothness(1)
        
        # Create the HPGL data
        paths = g.get_polyline()
        
        # Apply device specific settings
        if self.device['cutting_overlap'][1]:
            Plugin.apply_cutting_overlap(paths,self.device['cutting_overlap'][0])
        if self.device['cutting_blade_offset'][1]:
            Plugin.apply_cutting_blade_offset(paths,self.device['cutting_blade_offset'][0])

        data = []
        for path in paths:
            x,y = path.pop(0)[1]
            data.append('PU%i,%i'%(round(x),round(y)))
            cmd = "PD"
            for line in path:
                x,y = line[1]
                cmd +='%i,%i,'%(round(x),round(y))
            data.append(cmd[:-1])

        hpgl.extend(data)
        hpgl.extend(self.commands['send_after'])
        pos = self.plot['finish_position']
        hpgl.append('PU%i,%i'%(round(self.device['axis_scale'][0]*HPGL_SCALE*pos[0]),round(y*self.device['axis_scale'][1]*HPGL_SCALE*pos[1])))
        # Not friendly for large files!
        self.output =  ";\n".join(hpgl)+";"

class Import(Plugin):
    def __init__(self):
        super(Plugin,self).__init__()
        self.name = "HPGL"
        self.mode = "import"
        self.filetypes = ["hpgl"]

    def run(self):
        """ Converts HPGL into SVG """
        f = open(self.input)
        hpgl = f.read().replace('\n','').strip()
        f.close()

        # Generate the path data from the HPGL data
        pen_up = True
        pen_up_data = "M 0,0 "
        pen_down_data = ""
        for cmd in hpgl.split(';'):
            cmd,params = cmd[:2],cmd[2:]
            if cmd in ['PU','PD','PA']:
                if cmd == 'PU':pen_up = True                               
                elif cmd == 'PD':pen_up = False
                
                # According to HPGL command definitions these commands can have repeated coordinates.
                params = map(lambda x:float(x)/HPGL_SCALE,params.split(',')) # x,y[x,y[,...]]
                log.debug(map(round,params))
                
                # Generate the path that the pen moves for this command.
                d = 'L '
                for i in range(0,len(params),2):
                    d +='%i,%i '%(params[i],params[i+1])
                if pen_up:
                    pen_up_data += d
                    pen_down_data += 'M %i,%i '%(params[-2],params[-1])
                else:
                    pen_up_data += 'M %i,%i '%(params[-2],params[-1])
                    pen_down_data += d
                log.debug("Data: " +d)    

                
                    

        # Create the SVG using the HPGL path data
        svg = etree.fromstring(SVG)
        path = etree.Element('path')
        path.set('d',pen_up_data)
        path.set('style','fill:none; stroke: #36BFDC; stroke-dasharray: 9, 5;')
        svg.append(path)

        path = etree.Element('path')
        path.set('d',pen_down_data)
        svg.append(path)
        self.output = etree.tostring(svg)
        

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
