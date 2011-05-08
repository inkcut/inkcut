#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     	Inkcut, Plot HPGL directly from Inkscape.
#       plot.py
# ----------------------------------------------------------------------
#	Class for creating complex plots from a simple svg graphic.
#   A Graphic is created from a svg file.  The graphic is then added
#   to an svg representing a plot.  The graphic is cloned cloned,
#   spaced
# ----------------------------------------------------------------------
#   Copyright 2010 Jairus Martin <frmdstryr@gmail.com>
#   See liscense for liscensing info

from lib.geom import cubicsuperpath, simplepath, cspsubdiv, simpletransform,bezmisc
from lib.pysvg import parser, shape, structure, builders

class Plot:
    """
    Makes an svg the fulfills the job requriements
    """
	def __init__(self,material):
        w = material.get_width()
        l = material.get_length()
        
        # create the base svg (simulate the material)
        svg = structure.svg(width=unit(2,'cm')+w,height=unit(2,'cm')+l)
        
        # add the material layer
        layer = structure.g()
        layer.set_id('material_layer')
        layer.setAttribute('inkscape:label','Material Layer')
        layer.setAttribute('inkscape:groupmode','layer')
        layer.setAttribute('transform','translate(%f,%f)'%(unit(1,'cm'),unit(1,'cm')))
        svg.addElement(layer)
        self.set_material(material)
        
        # add the data layer
        layer = structure.g()
        layer.set_id('data_layer')
        layer.setAttribute('inkscape:label','Data Layer')
        layer.setAttribute('inkscape:groupmode','layer')
        layer.setAttribute('transform','translate(%f,%f)'%(unit(1,'cm'),unit(1,'cm')))
        svg.addElement(layer)
        self.svg = svg
        
    def get_preview_svg():
        return self.svg.getXML()
        
    def set_material(m):
        material = builders.ShapeBuilder().createRect(
                x=0,y=0,width=m.get_width(),height=m.get_length(),
                fill=m.get_color()
            )
        layer = self.svg.getElementByID('material_layer')
        layer._subElements = [] # bad!
        layer.addElement(material)
    
    def set_source(self,source):
        """
        Defines the graphic svg to be copied/scaled, should be a list
        of paths
        """
        svg = parser.parse(source)
        # TODO get source graphic height and width
        self.src = svg.getElementsByType(shape.path)
    
	def set_copies(self,n):
        """
        Makes n copies of a path, does nothing with position or path data
        """
        layer = self.svg.getElementByID('data_layer')
        layer._subElements = [] # bad!
        paths = self.src
        for i in range(0,len(paths)):
            copy = structure.g()
            copy.set_id("copy-%i"%(i))
            for path in paths:
                copy.addElement(path)
            layer.addElement(copy)
                
    def set_copy_positions(self):
        """
        Sets the x and y values of each copy
        """
        layer = self.svg.getElementByID('data_layer')
        for copy in layer.getAllElements():
            copy.setAttribute('transform','translate(%f,%f)'%(x,y))
    
