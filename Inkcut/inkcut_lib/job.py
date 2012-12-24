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
