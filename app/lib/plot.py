#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Inkcut, Plot HPGL directly from Inkscape.
#       plot.py
# ----------------------------------------------------------------------
#   Class for creating complex plots from a simple svg graphic.
#   A Graphic is created from a svg file.  The graphic is then added
#   to an svg representing a plot.  The graphic is cloned cloned,
#   spaced
# ----------------------------------------------------------------------
#   Copyright 2010 Jairus Martin <frmdstryr@gmail.com>
#   Released under GPL lisence

from lib.geom import inkex, cubicsuperpath, simplepath, cspsubdiv, simpletransform,bezmisc
from lib.pysvg import parser, shape, structure, builders
from lxml import etree

class Plot:
    """
    Makes an svg the fulfills the job requriements
    """
    def __init__(self,material):
        height = material.get_width()
        width = material.get_length()

        # create the base svg (simulate the material)
        #svg = structure.svg(width=unit(2,'cm')+width,height=unit(2,'cm')+height)
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

    def get_preview_svg(self,material):
        # make a new svg
        svg = etree.Element(inkex.addNS('svg','svg'))
        svg.set('version','1.1')
        svg.set('height',str(unit(2,'cm')+height))
        svg.set('width',str(unit(2,'cm')+width))

        # add the material layer
        layer = etree.Element(inkex.addNS('g','svg'))
        layer.set('id','inkcut_material_layer')
        layer.set('inkscape:label','Material')
        layer.set('inkscape:groupmode','layer')
        layer.set('transform','translate(%f,%f)'%(unit(1,'cm'),unit(1,'cm')))
        layer.set('x','0')
        layer.set('y','0')
        layer.set('width',str(material.get_height()))
        layer.set('height',str(material.get_length()))
        style = {'fill' : str(material.get_color()),'fill-opacity': '1','stroke':'#000000'}
        style = simplestyle.formatStyle(style)
        layer.set('style',style)

        # add the plot layer to the material layer
        plot = get_element_by_id(self.svg,'inkcut_plot_layer')
        layer.append(plot)
        svg.append(layer)

        return etree.tostring(svg)

    def set_graphic(self,svg):
        """
        Creates a Graphic from an input SVG string, return true if success
        or false if error message
        """
        self.graphic = Graphic(svg)

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
        layer = get_element_by_id(self.svg,'inkcut_plot_layer')
        for copy in layer.getAllElements():
            copy.setAttribute('transform','translate(%f,%f)'%(x,y))


class Graphic:
    """
    SVG graphic to be copied/scaled repositioned ect... from Inkcut 1.0
    """
    def __init__(self,svg):
        self.data = self.to_basic_paths(self.get_paths(svg))

        group = etree.Element(inkex.addNS('g','svg'))
        group.set('id','base_graphic')
        for path in paths:
            group.addElement(path)
        self.data = group

        # graphic properties
        self.bbox = self.get_bounding_box()
        self.height = self.get_height()
        self.width = self.get_width()
        #self.length = self.get_path_length()

    def get_paths(self,nodes):
        # takes in a list of lxml elements
        # returns a list of inkscape compound simplepaths (paths in paths etc...)
        if type(nodes) != type(list):
            nodes = list(nodes)
        spl = []
        for node in nodes:
            if node.tag in [ inkex.addNS('path','svg'), 'path' ]:
                spl.extend(simplepath.parsePath(node.get("d")))
            elif node.tag in [ inkex.addNS('rect','svg'), 'rect' ]:
                # TODO: Convert rect to path
                raise AssertionError("Cannot handle '%s' objects, covert to rect's to path first."%(tag))
            elif node.tag in [ inkex.addNS('g','svg'), 'g' ]:
                if node.get("transform"):
                    simpletransform.applyTransformToNode(node.get("transform"),node)
                spl.extend(self.get_paths(list(node)))
            else:
                raise AssertionError("Cannot handle tag '%s'"%(tag))
        return spl

    def to_basic_paths(self,spl):
        # break a complex path with subpaths into individual paths
        bpl = [] # list of basic paths
        i=-1
        for cmd in spl:
            if cmd[0]=='M': # start new path!
                bpl.append([cmd])
                i+=1
            else:
                bpl[i].append(cmd)
        return bpl

    # Properties --------------------------------------------------------------
    def get_height(self):
        bbox = self.get_bounding_box()
        return bbox[3]-bbox[2]

    def get_width(self):
        bbox = self.get_bounding_box()
        return bbox[1]-bbox[0]

    def get_bounding_box(self):
        # corner points of box
        return list(simpletransform.computeBBox(self.data)) # [minx,maxx,miny,maxy]

    def get_path_length(self):
        poly = self.to_polyline()
        i = 1
        d = 0
        while i < len(poly):
            last = poly[i-1][1]
            cur = poly[i][1]
            d += bezmisc.pointdistance(last,cur)
            i+=1
        return d

    # Export ------------------------------------------------------------------
    def to_polyline(self,path_smoothness):
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
        #pprint(poly)

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

    def set_scale(self):
        pass

    def set_mirror_x(self):
        pass

    def set_mirror_y(self):
        pass

    def set_rotation(self):
        pass

    def move_to_origin(self):
        pass

# lxml Shortcut Functions

def get_element_by_id(self,etreeElement, id):
        path = '//*[@id="%s"]' % id
        el_list = etreeElement.xpath(path, namespaces=inkex.NSS)
        if el_list:
          return el_list[0]
        else:
          return None

def get_selected_nodes(self,etreeElement,id_list):
        """Collect selected nodes"""
        nodes = []
        for id in id_list:
            path = '//*[@id="%s"]' % id
            for node in etreeElement.xpath(path, namespaces=inkex.NSS):
                nodes.append(node)
        return nodes
