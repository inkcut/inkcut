#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: plot.py
# Author: Copyright 2011 Jairus Martin <frmdstryr@gmail.com>
# Date: 27 July 2011
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
import math
from copy import deepcopy
from lxml import etree
from lib.geom import simpletransform
from graphic import Graphic, SVG
log = logging.getLogger(__name__)

class Plot:
    """
    A class representing a Plot. Includes methods for creating multiple copies
    of a graphic and positioning them on the plot.  Has plot wide path
    manipulation methods such as scaling, mirroring, rotating, and translating.
    Has the ability to create weedlines. Raises exceptions if the graphic or
    number of copies is too large for the material area.
    """
    def __init__(self,width,height=None,color='#FFFFFF'):
        """
        Creates the base plot properties and defines the plot material.
        """
        self.graphic = None
        self._data = []
        self._properties = {
            'copies': 1,
            'position':(0,0), # This relative position to get_start_position()
            'spacing': (9,9),
            'padding':  (35,0,35,0),
            'weedline':  False,
            'weedline_padding': 0,
            'axis_mirror_x': False,
            'axis_mirror_y': False,
            'axis_rotation': 0,
            'axis_scale': 1,
            'align_center_x': False,
            'align_center_y': False,
            'auto_rotate':False,
            'finish_position':(0,0), # Not implemented, used by higher level
        }
        self.set_material(width,height,color)

    # ================================ Export ================================
    def get_properties(self):
        """ Returns the properties used to build the plot. """
        return self._properties
        
    def get_data(self):
        """ Returns the data as a list of etree Elements. """
        elements = []
        for g in self._data:
            elements.append(g.get_data())
        return elements

    def get_xml(self):
        """Returns the data as an SVG string."""
        svg = etree.fromstring(SVG)
        layer = etree.Element('g')
        layer.set('id',unicode("plot.%s"% id(self)))
        layer.set('{http://www.inkscape.org/namespaces/inkscape}label','Plot')
        layer.set('{http://www.inkscape.org/namespaces/inkscape}groupmode','layer')
        layer.extend(self.get_data())
        svg.append(layer)
        return etree.tostring(svg,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=False)

    def get_preview_xml(self):
        """
        Creates a visual representation of the svg as it would look if it were
        plotted on the material.
        """
        svg = etree.fromstring(SVG)
        svg.set('width',unicode(self.get_material_width(limited=self.get_rotation()==90)+100))
        svg.set('height',unicode(self.get_material_height(limited=self.get_rotation()==0)+100))
        layer = etree.Element('g')
        layer.set('id','material')
        layer.set('{http://www.inkscape.org/namespaces/inkscape}label','Material')
        layer.set('{http://www.inkscape.org/namespaces/inkscape}groupmode','layer')
        layer.set('transform','translate(%f,%f)'%(35,35))
        layer.set('x','0')
        layer.set('y','0')
        layer.set('width',str(self.get_material_width(limited=self.get_rotation()==90)))
        layer.set('height',str(self.get_material_height(limited=self.get_rotation()==0)))
        vinyl = etree.Element('rect')
        vinyl.set('x','0')
        vinyl.set('y','0')
        vinyl.set('width',unicode(self.get_material_width(limited=self.get_rotation()==90)))
        vinyl.set('height',unicode(self.get_material_height(limited=self.get_rotation()==0)))
        vinyl.set('style',"fill:%s;"% self.get_material_color())
        shadow = deepcopy(vinyl)
        shadow.set('y','8')
        shadow.set('style',"fill:#000000;filter:url(#filter1);")
        layer.append(shadow)
        layer.append(vinyl)
        layer.extend(self.get_data())
        svg.append(layer)
        return etree.tostring(svg,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=False)

    # ================================ Properties ================================
    def get_material_width(self,limited=False):
        """
        Returns the plot x-size boundary or simulated material width as a float.
        If limited is set to True, this will return the total plot length, which is
        useful for eliminated lots of empty space on a preview.
        """
        if limited:
            return self.get_bounding_box()[1]+self.get_padding()[1] # maxx + right padding
        else:
            return self._material['width']

    def get_material_height(self,limited=False):
        """
        Returns the plot y-size boundary or simulated material height as a float.
        If limited is set to True, this will return the total plot length, which is
        useful for eliminated lots of empty space on a preview.
        """
        if limited:
            return self.get_bounding_box()[3]+self.get_padding()[2] # maxy + bottom padding
        else:
            return self._material['height']

    def get_material_color(self):
        """ Returns the material color as a string. """
        return self._material['color']

    def _get_available_bounding_box(self):
        """
        Returns the plottable bounding box of the material, or corner points of
        the area to be plotted on as a list in the format [minx,maxx,miny,maxy].
        """
        width, height = self.get_material_width(),self.get_material_height()
        top, right, bottom, left = self.get_padding()
        return [left,width-right,bottom,height-top]

    def get_available_width(self):
        """ Returns the plottable width (x-dimension) of the material. """
        bbox = self._get_available_bounding_box()
        return bbox[1]-bbox[0]

    def get_available_height(self):
        """ Returns the plottable height (y-dimension) of the material. """
        bbox = self._get_available_bounding_box()
        return bbox[3]-bbox[2]

    def get_start_position(self):
        """
        Convience method. Returns the starting point of the plottable area
        as a list in the form [minx,miny].
        """
        bbox = self._get_available_bounding_box()
        return [bbox[0],bbox[2]]

    def get_position(self,absolute=False):
        """
        Convience method. Returns the point upper left most point of the plot
        relative to get_start_position() as a list in the form [minx,miny].
        If absoulte is true, this returns the absolute position in the same form.
        This includes the plot weedline position.
        """
        pos = [0,0]
        out = self._properties['position']
        if absolute:
            pos = self.get_start_position()
        return (out[0]+pos[0],out[1]+pos[1])

    def get_bounding_box(self):
        """
        Returns the bounding box, or corner points of the plot as a list in
        the format [minx,maxx,miny,maxy].   This should always be within the
        available_bounding_box()!
        """
        if len(self._data) < 1:
            raise IndexError("No graphic data has been found.")
        else:
            bbox = self._data[0].get_bounding_box()
            for g in self._data:
                bbox = simpletransform.boxunion(g.get_bounding_box(),bbox)
            minx,maxx,miny,maxy = self._get_available_bounding_box()
            #assert (bbox[0] >= minx) and (bbox[1] <= maxx) and (bbox[2] >= miny) and (bbox[3] <= maxy), "The plot bounding box %s should always be within the available bounding box %s!" % (bbox, self._get_available_bounding_box())
            return bbox

    def get_height(self):
        """Returns the height (y-size) of the entire plot. """
        bbox = self.get_bounding_box()
        return bbox[3]-bbox[2]

    def get_width(self):
        """Returns the width (x-size) of the entire plot. """
        bbox = self.get_bounding_box()
        return bbox[1]-bbox[0]

    def get_padding(self):
        """Returns the padding set on the outside of the plot as a list [top,right,bottom,left]."""
        return self._properties['padding']

    def get_spacing(self):
        """Returns the spacing to be used between copies as a list [col_x,row_y]. """
        return self._properties['spacing']

    def get_stack_size_x(self,rotated=False):
        """
        Returns the number of graphics that fit within the
        get_available_width() as an int. If rotated=True, it returns the stack
        size if the graphic was rotated 90 degrees.
        """
        assert self.graphic, "A graphic must be set on this plot first!"
        needed = self.graphic.get_width()+self.get_spacing()[0]
        if rotated:
            needed = self.graphic.get_height()+self.get_spacing()[0]
        # The last spacing we don't need, adding spacing takes care of that.
        available = self.get_available_width()+self.get_spacing()[0]-self.get_position()[0]
        if self.get_weedline_status(): # allocate space for weedline padding if enabled
            available -= 2*self.get_weedline_padding()
        return int(math.floor(available/needed))

    def get_stack_size_y(self,rotated=False):
        """
        Returns the number of graphics that fit within the
        get_available_height() as an int. If rotated=True, it returns the stack
        size if the graphic was rotated 90 degrees.
        """
        assert self.graphic, "A graphic must be set on this plot first!"
        needed = self.graphic.get_height()+self.get_spacing()[1]
        if rotated:
            needed = self.graphic.get_width()+self.get_spacing()[1]
        # The last spacing we don't need, adding spacing takes care of that.
        available = self.get_available_height()+self.get_spacing()[1]-self.get_position()[1]
        if self.get_weedline_status(): # allocate space for weedline padding if enabled
            available -= 2*self.get_weedline_padding()
        return int(math.floor(float(available)/needed))

    def get_rotation(self):
        """
        Returns the degrees the plot has been rotated relative to the original.
        Designed for devices that use a rotated axis relative to the SVG spec.
        """
        return self._properties['axis_rotation']

    def get_copies(self):
        """ Returns the number of graphic copies to be created. """
        return self._properties['copies']

    def get_auto_rotate(self):
        """ Returns true if auto_rotate is enabled. """
        return self._properties['auto_rotate']

    def get_weedline_status(self):
        """ Returns true if a weedline is drawn around the plot."""
        return self._properties['weedline']

    def get_weedline_padding(self):
        """ Returns the weedline padding around the plot as a float."""
        return self._properties['weedline_padding']


    # ================================ Manipulation ================================
    def set_graphic(self,svg):
        """Sets the SVG graphic that is used in the plot. Returns False."""
        self.graphic = Graphic(svg,plot=self)
        if self.graphic.get_height() > self.get_available_height():
            h1, h2 = self.graphic.get_height(),self.get_available_height()
            self.graphic = None
            raise Exception("The height (%s) of this graphic is too large to fit on the material (%s). \n Please resize the graphic or choose a new material." %(h1,h2))
        elif self.graphic.get_width() > self.get_available_width():
            w1, w2 = self.graphic.get_width(),self.get_available_width()
            self.graphic = None
            raise Exception("The width (%s) of this graphic is too large to fit on the material (%s). \n Please resize the graphic or choose a new material." %(w1,w2))
        self.update()
        return False

    def set_position(self,x,y):
        """
        Sets where the top left corner of the plot is positioned relative to
        get_start_position(). Disables set_align_center_x() and
        set_align_center_y(). Returns False.
        """
        assert type(x) in [int,float] and type(y) in [int,float], "x and y must be an int or a float"
        assert x >= 0 and y >= 0 , "x and y must be 0 or more."
        log.debug("set_position(%s,%s)"%(x,y))
        pos = self.get_position() # update the properties
        if pos[0] != x: self._properties['align_center_x'] = False
        if pos[1] != y: self._properties['align_center_y'] = False
        if x != pos[0] or y != pos[1]:
            if self.graphic:
                if x+self.get_width() > self.get_available_width() or\
                    y+self.get_height() > self.get_available_height():
                    raise Exception("This will position the plot off of the material! \n Please resize the graphic or choose a new material.")
                else:
                    self._properties['position'] = (x,y)
                    self.update()
                    # check to make sure it was set right for debugging purposes
                    #pos = self.get_start_position()
                    #bbox = self.get_bounding_box()
                    #assert (round(bbox[0]-pos[0],10),round(bbox[2]-pos[1],10)) == (round(x,10),round(y,10)),"The position (%s,%s) was set incorrectly to (%s,%s)! \n If the problem persists, please contact the developer."%(round(x,10),round(y,10),round(bbox[0]-pos[0],10),round(bbox[2]-pos[1],10))
            else: # no graphic set the property so it's there for first time use
                self._properties['position'] = (x,y)
        return False

    def set_align_center_x(self,enabled):
        """
        If enabled, the plot is positioned to be centered horizontally
        in the get_available_width(). If disabled, resets to x to 0. Returns False.
        """
        assert self.graphic, "A graphic must be set on this plot first!"
        assert type(enabled) == bool, "enable must be a bool"
        log.debug("set_align_center_x(%s)"%enabled)
        x,y = self.get_position()
        if enabled:
            extra_space = self.get_available_width()-self.get_width()
            self.set_position(float(extra_space)/2,y)
            self._properties['align_center_x'] = True
        else:
            self.set_position(0,y)
            self._properties['align_center_x'] = False
        return False

    def set_align_center_y(self,enabled):
        """
        If enabled, the plot is positioned to be centered vertically in the
        get_available_height(). If disabled, resets to y to 0. Returns False.
        """
        assert self.graphic, "A graphic must be set on this plot first!"
        assert type(enabled) == bool, "enabled must be a bool."
        log.debug("set_align_center_y(%s)"%enabled)
        x,y = self.get_position()
        if enabled:
            extra_space = self.get_available_height()-self.get_height()
            self.set_position(x,float(extra_space)/2)
            self._properties['align_center_y'] = True
        else:
            self.set_position(x,0)
            self._properties['align_center_y'] = False
        return False

    def set_padding(self,top=None,right=None,bottom=None,left=None):
        """
        Sets the padding or distance between the materials bounding box and the
        plottable bounding box _get_available_bounding_box(). Similar to padding
        in the css box structure or printing margins. Returns False.
        """
        log.debug("set_padding(%s,%s,%s,%s)"%(top,right,bottom,left))
        updated = [top,right,bottom,left]
        pad = self.get_padding()
        for i in range(0,len(updated)):
            assert type(updated[i]) in [type(None),int,float],"%s must be of type int or float. Given %s" % (it,type(it))
            if type(updated[i]) == type(None):
                updated[i] = pad[i]
        if pad != updated:
            for it in updated:
                assert it >= 0, "padding must be at least 0."
            top,right,bottom,left = updated
            if top+bottom >= self.get_material_height():
                raise ValueError
            if left+right >= self.get_material_width():
                raise ValueError
            self._properties['padding'] = updated
            if self.graphic:
                self.update()
        return False

    def set_copies(self,n):
        """
        Makes n copies of a path and spaces them out on the plot. Raises a
        SizeError exception if n copies will not fit on the material with the
        current settings. Returns False.
        """
        assert type(n) == int, "n must be an integer value."
        assert n > 0, "n must be 1 or more."
        log.debug("set_copies(%s)"%n)
        if self.get_copies() != n:
            self._properties['copies'] = n
            if self.graphic:
                self.update()
        return False

    def set_spacing(self,x=None,y=None):
        """ Sets the spacing between columns (x) and rows (y). Returns False."""
        spacing = self.get_spacing()
        if x is None: x = spacing[0]
        if y is None: y = spacing[1]
        assert type(x) in [int, float], "x spacing must be an int or float."
        assert type(y) in [int, float], "y spacing must be an int or float."
        log.debug("set_spacing(%s,%s)"%(x,y))
        if x != spacing[0] or y != spacing[1]:
            self._properties['spacing'] = (x,y)
            self.update() # error checking in update!
        return False

    def set_weedline(self,enabled):
        """If enabled, a box is drawn around the entire plot. Returns False. """
        assert type(enabled) == bool, "enabled must be a bool"
        log.debug("set_weedline(%s)"%(enabled))
        if enabled != self.get_weedline_status(): # a change needs made:
            self._properties['weedline'] = enabled
            if self.graphic:
                self.update()
        return False

    def set_weedline_padding(self,padding):
        """
        Sets the padding between the weedline and plot. If the plot
        originally had a weedline the padding will be added immediately,
        otherwise it will be added the next time it is enabled. Returns False.
        """
        assert type(padding) in [int,float], "padding must be an int or float"
        assert padding >= 0, "padding must be 0 or more"
        log.debug("set_weedline_padding(%s)"%(padding))
        if padding != self.get_weedline_padding():
            self._properties['weedline_padding'] = padding
            if self.graphic:
                self.update()
        return False

    def set_rotation(self,degrees):
        """
        Set's the axis rotation of the material. If rotation = 90, the
        materials width and height will be swapped. This does not rotate the
        graphics or swap any padding/spacings. Returns False.
        """
        assert int(degrees) in [0,90], "The axis can only be rotated 0 or 90 degrees."
        log.debug("set_rotation(%s)"%(degrees))
        if degrees != self._properties['axis_rotation']:
            w = self.get_material_width()
            h = self.get_material_height()
            self._material['width'] = h # Swap them
            self._material['height'] = w
            self._properties['axis_rotation'] = degrees
            if self.graphic:
                self.update()
        return False

    def set_auto_rotate(self,enabled):
        """If enabled, graphics will be automatically rotated to save material. """
        assert type(enabled) == bool, "enabled must be a bool."
        log.debug("set_auto_rotate(%s)"%enabled)
        if enabled != self._properties['auto_rotate']:
            self._properties['auto_rotate'] == enabled
            if self.graphic:
                self.update()
        return False

    def set_cutting_order(self,mode=None):
        """ """
        assert mode in [None,'One copy at a time', 'Best tracking', 'Shortest Path']
        return False

    def set_material(self,width,height=None,color="#FFFFFF"):
        """ Set the width, length, and color of the plot. """
        assert type(width) in [int,float], "Material width must be an int or float, given %s."%type(width)
        assert type(height) in [type(None), int, float], "If the material has a limited height (length), it must be an int or float, otherwise set it to None.  Given %s" % type(length)
        assert type(color) in [str,unicode], "The material color must be a css style color (eg. #FFFFFF or \"white\"). Given %s." % type(color)
        assert width > 0, "Material width must be greater than 0, given %s."% width
        if height:
            assert height > 0, "Material height (length) must be greater than 0, given %s."% height
        else:
            height = 354330 # I'm just going to assume nobody will cut anything over 100 meters long!.
        self._material = {"width":width,"height":height,"color":color}
        if self.graphic:
            self.update()
        return False

    # ================================ Processing ================================
    def update(self):
        """
        Builds the plot from the graphic. Uses all the current properties.
        Raises exceptions if it cannot create the plot given the current
        values. This needs done whenever a property of self.graphic is changed.
        """
        # Check that there is enough room to fit all the copies.
        copies_left = self.get_copies()
        fit_x,fit_y = [self.get_stack_size_x(),self.get_stack_size_y()]
        rotate = False
        if fit_x*fit_y < copies_left:
            if self.get_auto_rotate():
                fit_x,fit_y = [self.get_stack_size_x(rotate=True),self.get_stack_size_y(rotate=True)]
            if fit_x*fit_y < copies_left:
                raise Exception("%s graphics are to be made but only %s will fit on the current material. Please adjust settings and try again." % (copies_left,fit_x*fit_y))
            else:
                rotate = True # This should only be set if the only way for it to fit is to rotate!

        # ==================== Generate the list of graphic positions, note that these are absolute.================================
        # positions, not relative to the plot padding like plot.set_position().
        x,y = self.get_position(absolute=True)

        if self.get_weedline_status():# If plot weedlines are enabled, we have to shift the graphics so the weedline fits.
            x += self.get_weedline_padding()
            y += self.get_weedline_padding()

        if rotate: self.graphic.set_rotation(90) # 90 should be a variable!
        dx,dy = self.graphic.get_width()+self.get_spacing()[0],self.graphic.get_height()+self.get_spacing()[1]
        positions = []
        if self.get_rotation() == 90: # Stack in positive x direction.
            while copies_left >= fit_y:
                for i in range(0,fit_y): # Fill a vertical stack.
                    positions.append([x,i*dy+y])
                # Add a new stack.
                x += dx
                copies_left -= fit_y

            # Fill leftover copies.
            for i in range(0,copies_left):
                positions.append([x,i*dy+y])

        else: # Stack in positive y direction.
            while copies_left >= fit_x:
                for i in range(0,fit_x): # Fill a horizontal stack.
                    positions.append([i*dx+x,y])
                # Add a new stack.
                y += dy
                copies_left -= fit_x

            # Fill leftover copies.
            for i in range(0,copies_left):
                positions.append([i*dx+x,y])

        # ==================== Create the plot from the given graphic positions ================================
        len_data = len(self._data) - (self.get_weedline_status() and 1 or 0)
        if self.graphic.get_changed_flag() or len(self._data)==0 or len_data != len(positions): # Only make new copies if the graphic changed
            self._data = []
            # Bugfix
            self.graphic._plot = None
            for pos in positions:
                x,y = pos
                g = deepcopy(self.graphic)
                g.set_position(x,y)
                self._data.append(g)
            self.graphic._plot = self
                
        else: # Just reposition the current data.  This should skip the weedline if it's enabled.
            for pos,g in zip(positions,self._data):
                x,y = pos
                g.set_position(x,y)
        if len(self._data) == self.get_copies()+1: # weedlines were previously enabled!
                self._data.pop()

        if self.get_weedline_status(): # add it to the data
            minx,maxx,miny,maxy = self.get_bounding_box()
            p = self.get_weedline_padding()
            d = "M%f,%f V%f H%f V%f Z" % (minx-p,miny-p,maxy+p,maxx+p,miny-p)
            svg = etree.fromstring(SVG)
            path = etree.Element('path')
            path.set('d',d)
            svg.append(path)
            g = Graphic(etree.tostring(svg))
            self._data.append(g)


#==============================================================================

class SizeError(Exception):
    """Exception raised when a graphic is too big for the material."""
    pass

class PositionError(Exception):
    """Exception raised when a plot is positioned off the material."""
    pass

#==============================================================================
