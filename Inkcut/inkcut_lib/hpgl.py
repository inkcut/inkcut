# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2011 Jairus Martin - Vinylmark LLC <jrm@vinylmark.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import logging
log = logging.getLogger('inkcut')

from filters import Filter
from helpers import get_unit_value
from plugin import Plugin
from graphic import Graphic,SVG
from lxml import etree

class SVGtoHPGL(Filter):
    name = "SVG to HPGL"
    infiletypes = ['svg']
    outfiletype = 'hpgl'

    def __init__(self,infile=None,outfile=None,preferences={}):
        """Inherit parent class and update properties specific to this filter."""
        super(SVGtoHPGL,self).__init__(infile,outfile,preferences)
        
    def run(self):
        """Converts an SVG file to an polyline HPGL file.
        Appends cutting speed and force commands as well as translates
        to origin if told to.
        """
        # Rename some preferences to make it easier to read
        device = self.preferences['device']
        units = self.preferences['units']
        plot = self.preferences['plot']

         # Set initial HPGL commands
        hpgl = ['IN;','SP1;']

        # If enabled , append Force and speed Commands
        if device['use_cutting_force']:
            hpgl.append('FS%i;'%get_unit_value(device['cutting_force'],units['force']))

        if device['use_cutting_speed']:
            hpgl.append('VS%d;'%get_unit_value(device['cutting_speed'],units['speed']))

        # Read the input SVG into a Graphic to provide easy manipulation and use built
        # in conversion to array/polylines.
        g = Graphic(self.infile)
        if not device['rotation']:
            g.set_mirror_x(True)
        # # The coordinate systems are flipped in HPGL from SVG
        # Scale it using calibration adjustments
        # See http://www.w3.org/TR/SVG/coords.html#Units and
        # http://en.wikipedia.org/wiki/HPGL
        # This should use
        HPGL_SCALE = get_unit_value(device['resolution'],units['resolution'])
        sx,sy = (device['cal_scale_x']*HPGL_SCALE,device['cal_scale_y']*HPGL_SCALE)
        g.set_scale(sx,sy)
		
        if plot['use_start_position']:
			x,y = get_unit_value(plot['start_x'],units['length']),get_unit_value(plot['start_y'],units['length'])
            device['rotation'] and g.set_position(y,x) or g.set_position(x,y)
        
        """
        # TODO: fix this
        elif plot['align_center_x']:
            g.set_position(0,0)
        elif plot['align_center_y']:
            g.set_position(0,0)
        """
        # Set how smooth the curves are, a high number may make lines look like
        # polygon lines.
        smoothness_map = {'Very High':0.05*HPGL_SCALE,'High':0.1*HPGL_SCALE,'Normal':0.2*HPGL_SCALE,'Low':0.4*HPGL_SCALE,'Very Low':0.8*HPGL_SCALE}
        smoothness = smoothness_map[device['curve_quality']]
        g.set_smoothness(smoothness)

        # This eliminates all curves, only use if you have to. Most (cheap) cutters 
        # don't support some of the curve HPGL commands so this is necessary.
        paths = g.get_data()
        
        # Apply device specific settings to the path, these methods do not support curves.
        
        if device['use_blade_offset']:
			offset = get_unit_value(device['blade_offset'],units['length'])*HPGL_SCALE
            self.apply_cutting_blade_offset(paths,offset,smoothness,angle=135)
        
        paths = g.get_polyline()
        if device['use_path_overcut']:
            self.apply_cutting_overcut(paths,get_unit_value(device['path_overcut'],units['length']))
        

        # Convert the SVG moveto and lineto commands to HPGL penup and pendown
        data = []
        for path in paths:
			if device['rotation']:
				y,x = path.pop(0)[1]
			else:
				x,y = path.pop(0)[1]
            data.append('PU%i,%i;'%(round(x),round(y)))
            for line in path:
				if device['rotation']:
					y,x = line[1]
				else:
					x,y = line[1]
                cmd ='PD%i,%i;'%(round(x),round(y))
                data.append(cmd)

        # Add the path data to the command list
        hpgl.extend(data)

        # Append the endpoint
        if plot['use_final_position']:
			x,y = round(get_unit_value(plot['final_y'],units['length'])*sy ),round(get_unit_value(plot['final_x'],units['length'])*sx)
			device['rotation'] and hpgl.append('PU%i,%i;'%(y,x)) or hpgl.append('PU%i,%i;'%(x,y))
            

        # Get output file and write the HPGL data to it
        # Note we could get rid of the command set and just write everything at once
        with open(self.outfile,'w') as out:
            if device['use_cmd_before']:
                out.write(device['cmd_before'])
            for cmd in hpgl:
                out.write(cmd)
            if device['use_cmd_after']:
                out.write(device['cmd_after'])
        
class HPGLtoSVG(Filter):
    name = "HPGL to SVG"
    infiletypes = ['hpgl']
    outfiletype = 'svg'

    def __init__(self,infile=None,outfile=None,preferences={}):
        """Inherit parent class and update properties specific to this filter."""
        super(HPGLtoSVG,self).__init__(infile,outfile,preferences)
        
    def run(self):
        """ Converts HPGL into SVG """
        HPGL_SCALE = get_unit_value(self.preferences['device']['resolution'],self.preferences['units']['resolution'])
        hpgl = []
        with open(self.infile) as f:
            for line in f:
                hpgl.extend(line.replace('\n','').strip().split(';'))
        
        # Generate the path data from the HPGL data
        pen_up = True
        pen_up_data = "M 0,0 "
        pen_down_data = ""
        for cmd in hpgl:
            cmd,params = cmd[:2],cmd[2:]
            if cmd in ['PU','PD','PA']:
                if cmd == 'PU':pen_up = True                               
                elif cmd == 'PD':pen_up = False
                
                # According to HPGL command definitions these commands can have repeated coordinates.
                params = map(lambda x:float(x)/HPGL_SCALE,params.split(',')) # x,y[x,y[,...]]
                
                # Generate the path that the pen moves for this command.
                d = 'L '
                for i in range(0,len(params),2):
                    d +='%f,%f '%(params[i],-params[i+1])
                if pen_up:
                    pen_up_data += d
                    pen_down_data += 'M %f,%f '%(params[-2],-params[-1])
                else:
                    pen_up_data += 'M %f,%f '%(params[-2],-params[-1])
                    pen_down_data += d
                #log.debug("Data: " +d)    

                
                    

        # Create the SVG using the HPGL path data
        svg = etree.Element('svg')
        g = etree.Element('g')
        g.set('id','inkcut_preview_%s'%self.infile)
        path = etree.Element('path')
        path.set('d',pen_up_data)
        path.set('style','fill:none; stroke: #36BFDC; stroke-width:0.5;')
        g.append(path)

        path = etree.Element('path')
        path.set('style','fill:none; stroke: #8A4F46; stroke-width:0.5;')
        path.set('d',pen_down_data)
        g.append(path)
        svg.append(g)
        with open(self.outfile,'w') as f:
            f.write(etree.tostring(svg))
