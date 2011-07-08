#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   App: Inkcut, Plot HPGL directly from Inkscape.
#   File: plot.py
#   Lisence: Copyright 2011 Jairus Martin, Released under GPL lisence
#   Author: Jairus Martin <frmdstryr@gmail.com>
#   Date: 2 July 2011
#   Changes:
#   moved Graphic to a new file...
#
import logging
from lxml import etree
from graphic import Graphic


log = logging.getLogger(__name__)

class Plot:
    """
    A class representing a Plot. Includes methods for creating multiple copies
    of a graphic and positioning them on the plot.  Has plot wide path
    manipulation methods such as scaling, mirroring, rotating, and translating.
    Has the ability to create weedlines. Raises exceptions if the graphic or
    number of copies is too large for the material area.
    """
    def __init__(self,width,height,color='#FFFFFF'):
        """Creates the base plot SVG and defines the plot material."""
        self._material = {'width':height,'length':width,'color':color}
        self.graphics = []
        self._properties = {
            'copies': 1,
            'spacing': [unit(.25,'cm'),unit(.25,'cm')],
            'padding':  [unit(1,'cm'),0,unit(1,'cm'),0],
            'axis_mirror_x': False,
            'axis_mirror_y': False,
            'axis_rotation': 0,
            'axis_scale': 1,
        }
        svg = etree.Element(inkex.addNS('svg','svg'))
        svg.set('version','1.1')
        svg.set('height',str(unit(2,'cm')+height))
        svg.set('width',str(unit(2,'cm')+width))

        # add the data layer
        layer = etree.Element(inkex.addNS('g','svg'))
        layer.set('id','inkcut_plot_layer')
        layer.set('inkscape:label','Plot')
        layer.set('inkscape:groupmode','layer')
        svg.append(layer)
        self.svg = svg

    def get_xml(self,material_length,material_width,material_color='#DDDDDD'):
        """
        Creates a visual representation of the svg as it would look if it were
        plotted on the material.
        """
        # make a new svg
        svg = etree.Element(inkex.addNS('svg','svg'))
        svg.set('version','1.1')
        svg.set('height',str(unit(2,'cm')+material_width))
        svg.set('width',str(unit(2,'cm')+material_length))

        # add the material layer
        layer = etree.Element(inkex.addNS('g','svg'))
        layer.set('id','inkcut_material_layer')
        layer.set('inkscape:label','Material')
        layer.set('inkscape:groupmode','layer')
        layer.set('transform','translate(%f,%f)'%(unit(1,'cm'),unit(1,'cm')))
        layer.set('x','0')
        layer.set('y','0')
        layer.set('width',str(material_width))
        layer.set('height',str(material_length))
        style = {'fill' : str(material_color),'fill-opacity': '1','stroke':'#000000'}
        style = simplestyle.formatStyle(style)
        layer.set('style',style)

        # add the plot layer to the material layer
        plot = get_element_by_id(self.svg,'inkcut_plot_layer')
        layer.append(plot)
        svg.append(layer)

        return etree.tostring(svg)

    # Properties --------------------------------------------------------------
    def _get_available_bounding_box(self):
        """
        Returns the plottable bounding box of the material, or corner points of
        the area to be plotted on as a list in the format [minx,maxx,miny,maxy].
        """
        width, height = self._material['length'],self._material['width']
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

    def get_position(self):
        """
        Convience method. Returns the point upper left most point of the plot
        as a list in the form [minx,miny].
        """
        bbox = self.get_bounding_box()
        return [bbox[0],bbox[2]]

    def get_bounding_box(self):
        """
        Returns the bounding box, or corner points of the plot as a list in
        the format [minx,maxx,miny,maxy].   This should always be within the
        available_bounding_box()!
        """
        bbox = [0,0,0,0]
        if !len(self.graphics):
            return bbox
        else:
            for g in self.graphics:
                bbox = simpletransform.boxunion(g.get_bounding_box(),bbox)
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

    def get_axis_mirror_x(self):
        """Returns true if the plot has been mirrored about the x-axis. """
        return self._properties['axis_mirror_x']

    def get_axis_mirror_y(self):
        """Returns true if the plot has been mirrored about the y-axis. """
        return self._properties['axis_mirror_y']

    def get_axis_rotation(self):
        """
        Returns the degrees the plot has been rotated relative to the original.
        Designed for devices that use a rotated axis relative to the SVG spec.
        """
        return self._properties['axis_rotation']

    def get_axis_scale(self):
        """
        Returns the scale of the plot relative to the original.  Designed to be
        used for a final device calibration scaling. Returns scale.
        """
        return self._properties['axis_scale']

    # Manipulation ------------------------------------------------------------
    def set_graphic(self,svg):
        """Sets the SVG graphic that is used in the plot. Returns Null."""
        self.graphics.append(Graphic(svg))

    def set_copies(self,n):
        """
        Makes n copies of a path and spaces them out on the plot. Raises a
        ValueError exception if n copies will not fit on the material with the
        given settings. Returns Null.
        """
        layer = self.svg.getElementByID('data_layer')
        layer._subElements = [] # bad!
        paths = self.src
        for i in range(0,len(paths)):
            copy = structure.g()
            copy.set_id("copy-%i"%(i))
            for path in paths:
                copy.addElement(path)
            layer.append(copy)

    def set_copy_positions(self):
        """
        Sets the x and y values of each copy
        """
        layer = get_element_by_id(self.svg,'inkcut_plot_layer')
        for copy in layer.getAllElements():
            copy.setAttribute('transform','translate(%f,%f)'%(x,y))

class SizeError(Exception):
    """Exception raised when a graphic is too big for the material."""
    pass



# lxml Shortcut Functions
def get_element_by_id(self,etreeElement, id):
        """Returns the first etree element with the given id"""
        assert type(etreeElement) == etree.Element, "etreeElement must be an etree.Element!"
        path = '//*[@id="%s"]' % id
        el_list = etreeElement.xpath(path, namespaces=inkex.NSS)
        if el_list:
          return el_list[0]
        else:
          return None

def get_selected_nodes(self,etreeElement,id_list):
        """Returns a list of nodes that have an id in the id_list."""
        assert type(etreeElement) == etree.Element, "etreeElement must be an etree.Element!"
        assert type(id_list) == id_list, "id_list must be a list of id's to search for"
        nodes = []
        for id in id_list:
            path = '//*[@id="%s"]' % id
            for node in etreeElement.xpath(path, namespaces=inkex.NSS):
                nodes.append(node)
        return nodes
