#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: graphic.py
# Author: Copyright 2011 Jairus Martin <frmdstryr@gmail.com>
# Date: 12 July 2011
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
from pprint import pprint
from geom import inkex, cubicsuperpath, simplepath, cspsubdiv, simpletransform,bezmisc
from lxml import etree
log = logging.getLogger(__name__)

SVG = """
<svg
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:cc="http://creativecommons.org/ns#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:svg="http://www.w3.org/2000/svg"
    xmlns="http://www.w3.org/2000/svg"
    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
    width="100%"
    height="100%"
    version="1.1">
    <defs>
        <style type="text/css">
            <![CDATA[
                path {fill: none;stroke: #000000;opacity:0.7}
            ]]>
        </style>
        <svg:filter id="filter1">
            <svg:feGaussianBlur id="feGaussianBlur1" stdDeviation="8"></svg:feGaussianBlur>
        </svg:filter>
    </defs>
    <metadata>
    <rdf:RDF>
      <cc:Work rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title></dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
</svg>
"""
class Graphic:
    """
    An class to represent an SVG graphic.  Includes methods for scaling,
    mirroring, rotating, and translating.  Gathers properties such as height,
    width, bounding box, and current position.
    """
    def __init__(self,svg,plot=None):
        """
        Creates a Graphic.  Takes svg as a string as a paramter, extracts all
        paths within the svg, and joins them into one simplepath.
        """
        assert type(svg) in [str, etree._ElementTree, etree._Element] , "svg must be an svg file, svg string, etree._Element, or etree._ElementTree"
        if type(svg) == str:
            try: 
                svg = etree.fromstring(svg)
            except etree.XMLSyntaxError:
                svg = etree.parse(svg)
        if type(svg) == etree._ElementTree:
            svg = svg.getroot()
        self._data = self._to_simplepaths(svg)

        # Used for automatically calling updates on the plot when a necessary change is made.
        self._plot = plot

        # Set the initial properties, these will be used by the manipulation
        # functions to keep a track of to the original state reversions are needed.
        self._properties = {
            'changed':True,
            'scale_x': 1,
            'scale_y': 1,
            'rotation': 0,
            'mirror_x': False,
            'mirror_y': False,
            'weedline': False,
            'weedline_padding': 0,
            'smoothness':0.02,
        }
        self._update_bounding_box()

    def _update(self):
        """
        If attached to a plot, the plot will automatically be updated when
        this function is called. Returns true on success.
        """
        if self._plot:
            try:
                self._plot.update()
                log.info("Plot.update() successfully triggered.")
                self.reset_changed_flag()
                return True
            except AttributeError:
                return False

    def _get_debug_data(self):
        """Returns self._data"""
        return self._data

    def get_properties(self):
        """ Returns the properties used to build the graphic. """
        return self._properties

    def get_data(self):
        """
        Breaks all paths up into basic paths. Returns the graphic as an etree
        element wrapped in group tags.
        """
        group = etree.Element('g')
        group.set('id',u"data.%s" %id(self))
        spl = self.get_data_array()
        for i in range(0,len(spl)):
            path = etree.Element('path')
            path.set('d',simplepath.formatPath(spl[i]))
            if self.get_weedline_status() and i==len(spl):
                path.set('class','weedline')
            group.append(path)
        return group

    def get_xml(self):
        """ Returns the graphic as an xml string. """
        svg = etree.fromstring(SVG)

        svg.append(self.get_data())
        return etree.tostring(svg,pretty_print=True,xml_declaration=True,encoding="UTF-8",standalone=False)

    # Properties --------------------------------------------------------------
    def get_changed_flag(self):
        """ Returns the graphic's changed flag as a bool."""
        return self._properties['changed']

    def _update_bounding_box(self):
        path = cubicsuperpath.parsePath(simplepath.formatPath(self._data))
        bbox = list(simpletransform.roughBBox(path))
        self._properties['bounding_box'] = bbox

    def get_bounding_box(self,adjusted=False):
        """
        Returns the bounding box, or corner points of the graphic as a list in
        the format [minx,maxx,miny,maxy]. If adjusted is true, the bounding box
        is adjusted to not include the weedline padding.
        """
        bbox = self._properties['bounding_box']
        if adjusted and self.get_weedline_status():
            pad = self.get_weedline_padding()
            bbox = [bbox[0],bbox[1]-2*pad,bbox[2],bbox[3]-2*pad]
        return bbox
        
    def get_height(self,adjusted=False):
        """
        Returns the height (y size) of the graphic. If adjusted is true,
        the height is adjusted to not include the weedline padding.
        """
        bbox = self.get_bounding_box(adjusted)
        return bbox[3]-bbox[2]

    def get_width(self,adjusted=False):
        """
        Returns the width (x size) of the graphic. If adjusted is true,
        the width is adjusted to not include the weedline padding.
        """
        bbox = self.get_bounding_box(adjusted)
        return bbox[1]-bbox[0]

    def get_mirror_x(self):
        """Returns true if the graphic has been mirrored about the x axis."""
        return self._properties['mirror_x']

    def get_mirror_y(self):
        """Returns true if the graphic has been mirrored about the y axis."""
        return self._properties['mirror_y']

    def get_rotation(self):
        """
        Returns the degrees the graphic has been rotated relative to the original.
        """
        return self._properties['rotation']

    def get_scale(self):
        """Returns the scale of the graphic relative to the original as a list [x,y]"""
        return [self._properties['scale_x'],self._properties['scale_y']]

    def get_position(self,adjusted=False):
        """
        Convience method. Returns the upper left most point of the graphic
        relative to the origin as a list [minx,miny].
        """
        bbox = self.get_bounding_box(adjusted)
        return [bbox[0],bbox[2]]

    def get_path_length(self,path=None):
        """ 
        Returns an estimate of the path length of the graphic. If
        path is supplied, it will return the length of that path only.
        """
        if path:
            assert type(path) == list, "path must be a list of path segments"
            paths = [path]
        else:
            paths = self.get_polyline()
        d = 0
        for path in paths:
            for i in range(0,len(path)-1):
                d += bezmisc.pointdistance(path[i][1],path[i+1][1])
        return d

    def get_weedline_status(self):
        """ Returns true if a weedline is drawn around the graphic."""
        return self._properties['weedline']

    def get_weedline_padding(self):
        """ Returns the weedline padding around the graphic as a float."""
        return self._properties['weedline_padding']

    def get_smoothness(self):
        """ Returns the weedline padding around the graphic as a float."""
        return self._properties['smoothness']

    # Conversion --------------------------------------------------------------
    def _to_simplepaths(self,nodes):
        """
        Takes in a list of etree._Elements and returns a list of simplepaths.
        """
        if type(nodes) != type(list):
            nodes = list(nodes)
        spl = []
        for node in nodes:
            if node.tag in [ inkex.addNS('path','svg'), 'path' ]:
                spl.extend(simplepath.parsePath(node.get("d")))
            elif node.tag in [ inkex.addNS('rect','svg'), 'rect' ]:
                # TODO: Convert rect to path
                log.warn("Cannot handle '%s' objects, covert to rect's to path first."%(node.tag))
            elif node.tag in [ inkex.addNS('g','svg'), 'g' ]:
                if node.get("transform"): # This doesn't work!
                    #simpletransform.applyTransformToPath(node.get("transform"),node)
                    pass
                spl.extend(self._to_simplepaths(list(node)))
            else:
                log.warn("Cannot handle tag '%s'"%(node.tag))
        return spl

    def get_polyline(self):
        """
        Converts the graphic into a path that has only contains straight lines.
        The smoothness is the maximum distance allowed between points in a
        curve. Returns the data as a list of paths.
        """
        smoothness=self.get_smoothness()
        def curveto(p0,curve,flat=smoothness):
            poly = []
            d = simplepath.formatPath([['M',p0],curve])
            p = cubicsuperpath.parsePath(d)
            cspsubdiv.cspsubdiv(p, flat)
            for sp in p:
                first = True
                for csp in sp:
                    if first:
                        first = False
                    else:
                        for subpath in csp:
                            poly.append(['L',list(subpath)])
            return poly

        paths = []
        for path in self.get_data_array():
            p = []
            for segment in path:
                cmd, params = segment
                if cmd in ['L','M']:
                    p.append(segment)
                    node = params
                elif cmd in ['C','A']:
                    p.extend(curveto(node,segment))
                    node = [params[-2],params[-1]]
                elif cmd == 'Z':
                    segment = ['L',path[0][1]]
                    p.append(segment)
            paths.append(p)

        """# remove double points
        last = poly[0][1]
        i = 1
        while i < len(poly)-1: # skip last
            cur = poly[i][1]
            if cur == last:
                poly.pop(i)
            i +=1
            last = cur[:]
        """
        return paths

    def get_data_array(self):
        """
        Converts a list of simplepaths that may have several moveto commands
        within each simplepath into a path that has only one moveto command per
        path.  Retuns a list of "basic" simplepaths.
        """
        paths = [] # list of basic paths
        i=-1
        for path in self._data:
            if path[0]=='M': # start new path!
                paths.append([path])
                i+=1
            else:
                paths[i].append(path)
        return paths

    # Manipulation ------------------------------------------------------------
    def reset_changed_flag(self):
        """ Sets the changed flag to false. """
        self._properties['changed'] = False

    def set_smoothness(self,smoothness):
        """ Set's the smoothness parameter of the bezier splines. """
        self._properties['smoothness'] = smoothness

    def set_scale(self,scale_x,scale_y=None):
        """Scales the graphic relative to the original. Returns False."""
        if scale_y is None:
            scale_y = scale_x
        assert type(scale_x) in [int,float], "scale_x must be an int or float"
        assert type(scale_y) in [int,float], "scale_y must be an int or float"
        assert scale_x > 0, "scale_x must be a postive value!"
        assert scale_y > 0, "scale must be a postive value!"
        sx,sy = self.get_scale()
        if sx != scale_x or sy != scale_y:
            simplepath.scalePath(self._data,float(scale_x)/sx,float(scale_y)/sy)
            self._update_bounding_box()
            self._properties['scale_x'] = scale_x
            self._properties['scale_y'] = scale_y
            self._properties['changed'] = True
            self._update()
        return False

    def set_mirror_x(self, enabled):
        """
        If enabled, the graphic is mirrored about the x axis. If false, the
        graphic will return to the original orentation. Returns False.
        """
        assert type(enabled) == bool, "enabled must be a bool"
        if enabled != self._properties['mirror_x']:
            x,y = self.get_position()
            simplepath.scalePath(self._data,1,-1) # flip it
            self._update_bounding_box()
            self.set_position(x,y)
            self._properties['mirror_x'] = enabled
            self._properties['changed'] = True
            self._update()
        return False

    def set_mirror_y(self, enabled):
        """
        If enabled, the graphic is mirrored about the y axis. If false, the
        graphic will return to the original orentation. Returns False.
        """
        assert type(enabled) == bool, "enabled must be a bool"
        if enabled != self._properties['mirror_y']:
            x,y = self.get_position()
            simplepath.scalePath(self._data,-1,1) # flip it
            self._update_bounding_box()
            self.set_position(x,y)
            self._properties['mirror_y'] = enabled
            self._properties['changed'] = True
            self._update()
        return False

    def set_rotation(self,degrees):
        """Rotates the graphic relative to the original.  Returns False."""
        assert type(degrees) in [int, float], "degrees must be an int or float"
        assert -360 < degrees < 360, "degrees must be between -359-359"
        last = self._properties['rotation']
        if (degrees != last):
            x,y = self.get_position()
            radians = (degrees-last)*math.pi/180
            simplepath.rotatePath(self._data, radians)
            self._update_bounding_box()
            self.set_position(x,y) # put it back to the same position it was before rotating!
            self._properties['rotation'] = degrees
            self._properties['changed'] = True
            self._update()
        return False

    def set_position(self,x,y):
        """
        Translates the graphic to the position x,y relative to the origin.
        Returns False. Note: This ignores the inital position of the graphic!
        """
        assert type(x) in [int,float], "x must be an int or float"
        assert type(y) in [int,float], "y must be an int or float"
        pos = self.get_position()
        simplepath.translatePath(self._data,x-pos[0],y-pos[1])
        self._update_bounding_box()
        return False

    def set_weedline(self,enabled):
        """ If enabled a box is drawn around the graphic. Returns False."""
        assert type(enabled) == bool, "enabled must be a bool"
        if enabled != self.get_weedline_status(): # a change needs made
            x,y = self.get_position()
            if enabled: # add it to the data
                # bbox should not include padding since the weedline is not yet enabled
                minx,maxx,miny,maxy = self.get_bounding_box()
                p = self.get_weedline_padding()
                d = "M%f,%f V%f H%f V%f Z" % (minx-p,miny-p,maxy+p,maxx+p,miny-p)
                self._data.extend(simplepath.parsePath(d))
            else: # remove it from the data
                for i in range(0,5): # remove the 5 commands added
                    self._data.pop()
            self._properties['weedline'] = enabled
            self._update_bounding_box()
            self.set_position(x,y)
            self._properties['changed'] = True
            self._update()
        return False

    def set_weedline_padding(self,padding):
        """
        Sets the padding between the weedline and graphic. If the graphic
        originally had a weedline the padding will be added immediately,
        otherwise it will be added the next time it is enabled. Returns None.
        """
        assert type(padding) in [int,float], "padding must be an int or float"
        assert padding >= 0, "padding must be 0 or more"
        if padding != self.get_weedline_padding():
            had_weedline = self.get_weedline_status()
            self.set_weedline(False)
            self._properties['weedline_padding'] = padding
            self.set_weedline(had_weedline)
            # updated in set_weedline
        return False




