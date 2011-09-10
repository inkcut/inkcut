#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       File: job.py
#       Date: 11 March 2011
#
#       Copyright 2011 Jairus Martin <jrm5555@psu.edu>
#
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
import os
from datetime import datetime
from plot import Plot
from lxml import etree
from unit import UNITS

# Database model
from sqlalchemy import Table, Column, Integer, DateTime, Unicode, ForeignKey,PickleType
from meta import Base

class Job(Base):
    """
    Job specificiations, properties, and requirements for converting
    from a graphic to the output format.  Interacts with a database
    to keep track of jobs.
    """
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    created = Column(DateTime,default=datetime.now())
    source_filename = Column(Unicode,unique=True)
    properties = Column(PickleType)
    units = Column(Unicode)
    source_selected_nodes = Column(PickleType)
    material_id = Column(Integer, ForeignKey('materials.id'))

    def __init__(self,
            id=None,
            name=None,
            description=None,
            created=None,
            material_id=None,
            units='cm',
            ):
        """
        Create a job instance with it's properties.
        """
        self.id = id
        self.name = unicode(name)
        self.created = created
        self.material_id = material_id
        self.properties = {
            'plot':{},
            'graphic':{}
        }

        # Push into material
        self.units = units

        self.status = u'Unsaved'
        self.messages = []

    # Job managment
    def set_source(self,source,nodes=None):
        """
        Handles opening a new file. Creates a plot with the given source
        file. Uses input plugins to convert file to SVG. This disregards
        all previous settings, thus ui_updates should be called.
        """
        height = self.material.length and self.material.length*UNITS[self.units] or None
        p = Plot(width=self.material.width*UNITS[self.units],height=height,color=self.material.color)
        m = self.material.margin
        p.set_padding(top=m[0],right=m[1],bottom=m[2],left=m[3])
        if type(source) == etree._ElementTree:
            try:
                # If certain nodes are selected, only plot them.
                if nodes:
                    xml = etree.tostring(get_selected_nodes(source,nodes))
                else:
                    xml = etree.tostring(source)
                # Set a job name if none exists
                if self.name is None:
                    self.name = "*inkscape.svg"
                # Try to make a plot
                p.set_graphic(xml)
                self.plot = p
            except (IOError,etree.XMLSyntaxError),trace:
                log.debug(trace)
                raise Exception("Failed to create plot. Reason: Failed to import the Inkscape file.")
        elif os.path.isfile(source):
            try:
                # Set job name from the source filename
                filename = os.path.split(source)[-1]
                self.name = "%s"%filename
                # Determine if input plugins are required.
                ext = filename.split('.')[-1]
                if ext.strip().lower() == 'svg': # no plugin is needed
                    p.set_graphic(source)
                    self.plot = p
                # TODO: Handle import plugins here!!
                # plugin = Inkcut.plugin(ext=ext,mode='input')
                # elif plugin:
                #   p.set_graphic(plugin.output)
                # else:
                # raise Exception("Failed to create plot. Reason: No import plugin found for extension: %s" % ext)
            except (IOError,etree.XMLSyntaxError),trace:
                log.debug(trace)
                raise Exception('Failed to create plot. Reason: Could not open the file: %s. Invalid file or file not found.'% source)
        else:
            try:
                # Set a job name if none exists
                if self.name is None:
                    self.name = "*inkscape.svg"
                p.set_graphic(source)
                self.plot = p
            except etree.XMLSyntaxError,trace:
                log.debug(trace)
                raise Exception('Failed to create plot. Reason: Invalid graphic source: '% source)

    def update_properties(self):
        if self.plot:
            self.set_properties('plot',self.plot.get_properties())
            self.set_property('plot','width',self.plot.get_width())
            self.set_property('plot','height',self.plot.get_height())
            self.set_properties('graphic',self.plot.graphic.get_properties())
    
    def set_property(self,group, property,value):
        """ Set's the a value in the job properties. """
        if group not in self.properties.keys():
            self.properties[group] = {}
        self.properties[group][property] = value

    def set_properties(self,group,values):
        """ Set's multiple values in the job properties. """
        assert type(values) == dict, "values must be a dict!"
        if group in self.properties.keys():
            self.properties[group].update(values)
        else:
            self.properties[group] = values

    def get_property(self,group, property):
        """ Fetches a value in the job properties. """
        return self.properties[group][property]

    def get_properties(self,group):
        """ Fetches a value in the job properties. """
        return self.properties[group]

    def set_material(self,material):
        self.material = material
        if self.plot is not None:
            height = self.material.length and self.material.length*UNITS[self.units] or None
            m = self.material.margin
            self.plot.set_padding(top=m[0],right=m[1],bottom=m[2],left=m[3])
            self.plot.set_material(width=self.material.width*UNITS[self.units],height=height,color=self.material.color)

    def set_plot_settings(self,settings={}):
        pass

    def get_plot_settings(self):
        pass

    def get_estimated_cost(self):
        pass

    def get_estimated_time(self):
        pass

    def submit(self):
        """
        Submits a job to be handled by the job device. Returns a status.
        """
        self.process()
        if self.validate():
            self.status = 'Sending to device...'
            self.device.submit(self.data)

        pass


#class JobRequirements(Base):
    #"""
    #Job requirements, so it can be easily changed it's separated from
    #the job
    #"""
    #__tablename__ = 'job_requirements'
    #id = Column(Integer, primary_key=True)
    #copies = Column(Integer)
    #scale = Column(Float)
    #start_x = Column(Integer)
    #start_y = Column(Integer)
    #center_x = Column(Boolean)
    #center_y = Column(Boolean)
    #invert_axis_x = Column(Boolean)
    #invert_axis_y = Column(Boolean)
    #plot_margin_top = Column(Float)
    #plot_margin_right = Column(Float)
    #plot_margin_bottom = Column(Float)
    #plot_margin_left = Column(Float)
    #copy_spacing_x = Column(Float)
    #copy_spacing_y = Column(Float)
    #copy_rotation = Column(Float)
    #path_smoothness = Column(Float)
    #path_sort_order = Column(Integer)
    #weed_plot = Column(Boolean)
    #weed_plot_margin = Column(Float)
    #weed_copy = Column(Boolean)
    #weed_copy_margin = Column(Float)
    #plot_selected_nodes = Column(UnicodeText)

    #def __init__(self,
            #id=None,
            #copies=1,
            #scale=1,
            #start_x=0,
            #start_y=0,
            #center_x=False,
            #center_y=False,
            #invert_axis_x=True,
            #invert_axis_y=False,
            #plot_margin_top=0,
            #plot_margin_right=0,
            #plot_margin_bottom=0,
            #plot_margin_left=0,
            #copy_spacing_x=unit(.25,'cm'), # TODO: load from config
            #copy_spacing_y=unit(.25,'cm'), # TODO: load from config
            #copy_rotation=0,
            #path_smoothness=0.2,
            #path_sort_order=0,
            #weed_plot=False,
            #weed_plot_margin=0,
            #weed_copy=False,
            #weed_copy_margin=0,
            #plot_selected_nodes=None
        #):
        ## Job requirements
        #self.copies = copies
        #self.scale = scale
        #self.start_x = start_x
        #self.start_y = start_y
        #self.center_x = center_x
        #self.center_y = center_y
        #self.invert_axis_x = invert_axis_x
        #self.invert_axis_y = invert_axis_y
        #self.plot_margin_top = plot_margin_top
        #self.plot_margin_right = plot_margin_right
        #self.plot_margin_bottom = plot_margin_bottom
        #self.plot_margin_left = plot_margin_left
        #self.copy_spacing_x = copy_spacing_x
        #self.copy_spacing_y = copy_spacing_y
        #self.copy_rotation = copy_rotation
        #self.path_smoothness = path_smoothness
        #self.path_sort_order = path_sort_order
        #self.weed_plot = weed_plot
        #self.weed_plot_margin = weed_plot_margin
        #self.weed_copy = weed_copy
        #self.weed_copy_margin = weed_copy_margin
        #self.plot_selected_nodes = plot_selected_nodes

        ## Job status flags
        #self.changed = True

        ## Setting Requirements
        #def set_copies(self,n):
            #assert n >= 1
            #self.copies = n

        #def set_scale(self,r):
            #assert r > 0
            #self.scale = r

        #def set_start_position(self,x,y):
            #assert x > 0
            #assert y > 0
            #self.start_x = x
            #self.start_y = y

        #def set_auto_center(self,enable_x,enable_y):
            #assert bool == type(enable_x)
            #assert bool == type(enable_y)
            #self.center_x = enable_x
            #self.center_y = enable_y

        #def set_invert_axis(self,enable_x,enable_y):
            #assert bool == type(enable_x)
            #assert bool == type(enable_y)
            #self.invert_axis_x = enable_x
            #self.invert_axis_y = enable_y

        #def set_plot_margin(self,top,right,bottom,left):
            #assert top >= 0
            #assert right >= 0
            #assert bottom >= 0
            #assert left >= 0
            #self.plot_margin_top = top
            #self.plot_margin_right = right
            #self.plot_margin_bottom = bottom
            #self.plot_margin_left = left

        #def set_copy_spacing(self,x,y):
            #self.copy_spacing_x = x
            #self.copy_spacing_y = y

        #def set_path_smoothness(self,s):
            #assert s >= .01
            #self.path_smoothness = s

        #def set_path_sort_order(self,order):
            ##assert order in ['One copy at a time']
            #self.path_sort_order = order

        #def set_weed_plot(self,enabled,margin):
            #assert bool == type(enabled)
            #assert min([self.plot_margin_top,self.plot_margin_right,self.plot_margin_bottom,self.plot_margin_left]) > margin > 0
            #self.weed_plot = enabled
            #self.weed_plot_margin = margin

        #def set_weed_copy(self,enabled,margin):
            #assert bool == type(enabled)
            #assert min([self.plot_margin_top,self.plot_margin_right,self.plot_margin_bottom,self.plot_margin_left]) > margin > 0
            #self.weed_copy = enabled
            #self.weed_copy_margin = margin



# lxml shortcut functions, should be pushed into a different file!
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
