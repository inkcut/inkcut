#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   App: Inkcut, Plot HPGL directly from Inkscape.
#   File: graphic.py
#   Lisence: Copyright 2011 Jairus Martin, Released under GPL lisence
#   Author: Jairus Martin <frmdstryr@gmail.com>
#   Date: 2 July 2011
#   Changes: Documented everthing, added assertions...
import logging
import math
from pprint import pprint
from lib.geom import inkex, cubicsuperpath, simplepath, cspsubdiv, simpletransform,bezmisc
from lxml import etree
log = logging.getLogger(__name__)
class Graphic:
    """
    An class to represent an SVG graphic.  Includes methods for scaling,
    mirroring, rotating, and translating.  Gathers properties such as height,
    width, bounding box, and current position.
    """
    def __init__(self,svg):
        """
        Creates a Graphic.  Takes svg as a string as a paramter, extracts all
        paths within the svg, and joins them into one simplepath.
        """
        assert type(svg) in [str, etree._ElementTree, etree._Element] , "svg must be an xml string or an etree._Element or etree._ElementTree"
        if type(svg) == str:
            svg = etree.fromstring(svg)
        if type(svg) == etree._ElementTree:
            svg = svg.getroot()
        self.data = self._to_simplepaths(svg)

        # Set the initial properties, these will be used by the manipulation
        # functions to keep a track of to the original state reversions are needed.
        self._properties = {
            'scale': 1,
            'rotation': 0,
            'mirror_x': False,
            'mirror_y': False,
            'weedline': False,
            'weedline_padding': 0
        }

    def _get_debug_data(self):
        """Returns self.data"""
        return self.data

    def get_data(self):
        """
        Breaks all paths up into basic paths. Returns the graphic as an etree
        element wrapped in group tags.
        """
        group = etree.Element(inkex.addNS('g','svg'))
        group.set('id','base_graphic')

        for sp in self._to_basic_paths():
            path = etree.Element(inkex.addNS('path','svg'))
            path.set('d',simplepath.formatPath(sp))
            group.append(path)
        return group

    def get_xml(self):
        """ Returns the graphic as an xml string. """
        svg = etree.Element(inkex.addNS('svg','svg'))
        svg.set('version','1.1')
        svg.append(self.get_data())
        return etree.tostring(svg)

    # Properties --------------------------------------------------------------
    def get_bounding_box(self,adjusted=False):
        """
        Returns the bounding box, or corner points of the graphic as a list in
        the format [minx,maxx,miny,maxy]. If adjusted is true, the bounding box
        is adjusted to not include the weedline padding.
        """
        had_weedline = self.get_weedline_status()
        if adjusted:
            self.set_weedline(False) # removes weedline if it is enabled
        path = cubicsuperpath.parsePath(simplepath.formatPath(self.data))
        self.set_weedline(had_weedline) # adds weedline back if it was enabled
        return list(simpletransform.roughBBox(path))

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
        """Returns the scale of the graphic relative to the original."""
        return self._properties['scale']

    def get_position(self,adjusted=False):
        """
        Convience method. Returns the upper left most point of the graphic
        relative to the origin as a list [minx,miny].
        """
        bbox = self.get_bounding_box(adjusted)
        return [bbox[0],bbox[2]]

    def get_path_length(self):
        """ Returns an estimate of the path length of the graphic. """
        poly = self._to_polyline()
        i = 1
        d = 0
        while i < len(poly):
            last = poly[i-1][1]
            cur = poly[i][1]
            d += bezmisc.pointdistance(last,cur)
            i+=1
        return d

    def get_weedline_status(self):
        """ Returns true if a weedline is drawn around the graphic."""
        return self._properties['weedline']

    def get_weedline_padding(self):
        """ Returns the weedline padding around the graphic as a float."""
        return self._properties['weedline_padding']

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
                    simpletransform.applyTransformToNode(node.get("transform"),node)
                spl.extend(self._to_simplepaths(list(node)))
            else:
                log.warn("Cannot handle tag '%s'"%(node.tag))
        return spl

    def _to_polyline(self,path_smoothness=0.02):
        """
        Converts the graphic into a path that has only contains straight lines.
        The smoothness is the maximum distance allowed between points in a
        curve. Returns the data as a cubic simple path.
        """
        smoothness = path_smoothness
        def curveto(p0,curve,flat):
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

        poly = []
        last = self.data[0][1][:]  # start position
        for i in range(0,len(self.data)):
            cmd = self.data[i][0]
            params = self.data[i][1]
            if cmd=='L' or cmd=='M':
                poly.append([cmd,params])
                last = params
            elif cmd=='C':
                poly.extend(curveto(last,[cmd,params],smoothness))
                last = [params[4],params[5]]
            elif cmd=='A':
                poly.extend(curveto(last,[cmd,params],smoothness))
                last = [params[5],params[6]]
            elif cmd=='Z': #don't know
                    #poly.append(['L',self.data[0][1][:]])
                    last = last
            else: #unknown?
                raise AssertionError("Polyline only handles, (L, C, A,& Z) path cmds, given %s"%(cmd))

        # remove double points
        last = poly[0][1]
        i = 1
        while i < len(poly)-1: # skip last
            cur = poly[i][1]
            if cur == last:
                poly.pop(i)
            i +=1
            last = cur[:]

        return poly

    def _to_basic_paths(self):
        """
        Converts a list of simplepaths that may have several moveto commands
        within each simplepath into a path that has only one moveto command per
        path.  Retuns a list of "basic" simplepaths.
        """
        spl = self.data
        bpl = [] # list of basic paths
        i=-1
        for cmd in spl:
            if cmd[0]=='M': # start new path!
                bpl.append([cmd])
                i+=1
            else:
                bpl[i].append(cmd)
        return bpl

    # Manipulation ------------------------------------------------------------
    def set_scale(self,scale):
        """Scales the graphic relative to the original. Returns None."""
        assert type(scale) in [int,float], "scale must be an int or float"
        assert scale > 0, "scale must be a postive value!"
        last = self._properties['scale']
        simplepath.scalePath(self.data,float(scale)/last,float(scale)/last)
        self._properties['scale'] = scale

    def set_mirror_x(self, enabled):
        """
        If enabled, the graphic is mirrored about the x axis. If false, the
        graphic will return to the original orentation. Returns None.
        """
        assert type(enabled) == bool, "enabled must be a bool"
        if enabled != self._properties['mirror_x']:
            x,y = self.get_position()
            simplepath.scalePath(self.data,1,-1) # flip it
            self.set_position(x,y)
            self._properties['mirror_x'] = enabled

    def set_mirror_y(self, enabled):
        """
        If enabled, the graphic is mirrored about the y axis. If false, the
        graphic will return to the original orentation. Returns None.
        """
        assert type(enabled) == bool, "enabled must be a bool"
        if enabled != self._properties['mirror_y']:
            x,y = self.get_position()
            simplepath.scalePath(self.data,-1,1) # flip it
            self.set_position(x,y)
            self._properties['mirror_y'] = enabled

    def set_rotation(self,degrees):
        """Rotates the graphic relative to the original.  Returns None."""
        assert type(degrees) in [int, float], "degrees must be an int or float"
        assert -360 < degrees < 360, "degrees must be between -359-359"
        last = self._properties['rotation']
        if (degrees != last):
            x,y = self.get_position()
            radians = (degrees-last)*math.pi/180
            simplepath.rotatePath(self.data, radians)
            self.set_position(x,y) # put it back to the same position it was before rotating!
            self._properties['rotation'] = degrees

    def set_position(self,x,y):
        """
        Translates the graphic to the position x,y relative to the origin.
        Returns None. Note: This ignores the inital position of the graphic!
        """
        assert type(x) in [int,float], "x must be an int or float"
        assert type(y) in [int,float], "y must be an int or float"
        pos = self.get_position()
        simplepath.translatePath(self.data,x-pos[0],y-pos[1])

    def set_weedline(self,enabled):
        """ If enabled a box is drawn around the graphic. Returns None."""
        assert type(enabled) == bool, "enabled must be a bool"
        if enabled != self.get_weedline_status(): # a change needs made
            x,y = self.get_position()
            if enabled: # add it to the data
                # bbox should not include padding since the weedline is not yet enabled
                minx,maxx,miny,maxy = self.get_bounding_box()
                p = self.get_weedline_padding()
                d = "M%f,%f V%f H%f V%f Z" % (minx-p,miny-p,maxy+p,maxx+p,miny-p)
                self.data.extend(simplepath.parsePath(d))
            else: # remove it from the data
                for i in range(0,5): # remove the 5 commands added
                    self.data.pop()
            self._properties['weedline'] = enabled
            self.set_position(x,y)

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



