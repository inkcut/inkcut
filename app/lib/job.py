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
from datetime import datetime
from unit import unit
from plot import Plot

# Database model
from sqlalchemy import Table, Column, Integer, Float, UnicodeText,DateTime, Unicode, ForeignKey, Boolean,Text
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
    description = Column(UnicodeText)
    created = Column(DateTime,default=datetime.now())
    source_filename = Column(Unicode,unique=True)
    source_last_modified = Column(DateTime)
    source = Column(Text,nullable=False)
    selected_nodes = Column(Text)
    data = Column(Text)
    status = Column(Unicode)
    device_id = Column(Integer, ForeignKey('devices.id'))
    material_id = Column(Integer, ForeignKey('materials.id'))
    requirements_id = Column(Integer, ForeignKey('job_requirements.id'))

    def __init__(self,
            id=None,
            name=None,
            description=None,
            created=datetime.now(),
            source_filename=None,
            source_last_modified=None,
            source=None,
            data=None,
            status=None,
            device_id=None,
            material_id=None,
            requirements_id=None,
            selected_nodes=None,
            ):
        """
        Create a job instance with it's properties.
        """
        self.id = id
        self.name = unicode(name)
        self.description = unicode(description)
        self.created = created
        self.source_filename = unicode(source_filename) # original graphic source filename
        self.source_last_modified = source_last_modified
        self.source = source # original graphic source file
        self.selected_nodes = selected_nodes
        self.data = data # inkcut created and modified svg
        self.status = unicode(status)
        self.device_id = device_id
        self.material_id = material_id

        # Job requirements
        if requirements_id is None:
            self.requirements = JobRequirements()
            self.requirements_id = self.requirements.id
        else:
            self.requirements_id = requirements_id


        # Job status flags
        self.status = u'Unprocessed'
        self.messages = []

        # Job properties
        self.plot_width = 0
        self.plot_length = 0
        self.copy_width = 0
        self.copy_length = 0
        self.path_length = 0
        self.estimated_cost = None
        self.estimated_time = None


    # Job managment
    def load(self):
        """ Parses the source file into an etree object. """
        if type(self.source) == etree._ElementTree:
            self.source = etree.tostring(self.source)
            self.process()
            return True
        elif self.source_filename is not None:
            try:
                self.source = open(self.source_filename).read()
                self.process()
                return True
            except (IOError,etree.XMLSyntaxError):
                self.messages.append('Could not open the file: %s. \n Reason: Invalid filetype or file not found.'% self.source_filename)
                return False

        self.messages.append('Could not open the source file.')
        return False

    def set_material():
        pass

    def set_device():
        pass

    # Job processing
    def process(self):
        """
        Converts the source svg to data svg using job requirements.
        """
        req = self.requirements
        plot = Plot(material)
        plot.set_graphic(self.source)
        plot.set_selected_nodes(req.plot_selected_nodes)
        plot.set_margin(req.plot_margin_top,req.plot_margin_right,req.plot_margin_bottom,req.plot_margin_left)
        plot.set_scale(req.scale_x*(invert_axis_x and 1 or -1),req.scale_y*(invert_axis_y and 1 or -1))
        plot.set_copy_spacing(req.copy_spacing_x,req.copy_spacing_y)
        plot.set_copies(req.copies)
        plot.create()


        self.data = self.source

    def get_preview_svg(self):
        """
        Returns a svg preview of the job.
        """
        w = self.material.get_width()
        l = self.material.get_length()

        # create the base svg (simulate the material)
        svg = structure.svg(width=unit(2,'cm')+w,height=unit(2,'cm')+l)

        # add the material layer
        layer = structure.g()
        layer.set_id('material_layer')
        layer.setAttribute('inkscape:label','Material Layer')
        layer.setAttribute('inkscape:groupmode','layer')
        material = builders.ShapeBuilder().createRect(
                x=unit(1,'cm'),y=unit(1,'cm'),width=w,height=l,
                fill=self.material.get_color()
            )
        layer.addElement(material)
        svg.addElement(layer)

        # add the data layer
        layer = structure.g()
        layer.set_id('data_layer')
        layer.setAttribute('inkscape:label','Data Layer')
        layer.setAttribute('inkscape:groupmode','layer')
        data = parser.parse_string(self.data)
        data.set_x(unit(1,'cm'))
        data.set_y(unit(1,'cm'))
        for path in data.getElementsByType(shape.path):
            layer.addElement(path)
        svg.addElement(layer)
        return svg.getXML()

    def validate(self):
        """
        Checks that the job can be done given the material and device.
        Returns boolean, appends any errors and dispatches messages
        """
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

    # Job properties
    def properties(self):
        """ Returns a dictionary of the job properties """
        return {'height': None, 'width': None,  'length': 0}

    def status(self):
        """ Returns job status """
        return self.status

class JobRequirements(Base):
    """
    Job requirements, so it can be easily changed it's separated from
    the job
    """
    __tablename__ = 'job_requirements'
    id = Column(Integer, primary_key=True)
    copies = Column(Integer)
    scale = Column(Float)
    start_x = Column(Integer)
    start_y = Column(Integer)
    center_x = Column(Boolean)
    center_y = Column(Boolean)
    invert_axis_x = Column(Boolean)
    invert_axis_y = Column(Boolean)
    plot_margin_top = Column(Float)
    plot_margin_right = Column(Float)
    plot_margin_bottom = Column(Float)
    plot_margin_left = Column(Float)
    copy_spacing_x = Column(Float)
    copy_spacing_y = Column(Float)
    copy_rotation = Column(Float)
    path_smoothness = Column(Float)
    path_sort_order = Column(Integer)
    weed_plot = Column(Boolean)
    weed_plot_margin = Column(Float)
    weed_copy = Column(Boolean)
    weed_copy_margin = Column(Float)
    plot_selected_nodes = Column(UnicodeText)

    def __init__(self,
            id=None,
            copies=1,
            scale=1,
            start_x=0,
            start_y=0,
            center_x=False,
            center_y=False,
            invert_axis_x=True,
            invert_axis_y=False,
            plot_margin_top=0,
            plot_margin_right=0,
            plot_margin_bottom=0,
            plot_margin_left=0,
            copy_spacing_x=unit(.25,'cm'), # TODO: load from config
            copy_spacing_y=unit(.25,'cm'), # TODO: load from config
            copy_rotation=0,
            path_smoothness=0.2,
            path_sort_order=0,
            weed_plot=False,
            weed_plot_margin=0,
            weed_copy=False,
            weed_copy_margin=0,
            plot_selected_nodes=None
        ):
        # Job requirements
        self.copies = copies
        self.scale = scale
        self.start_x = start_x
        self.start_y = start_y
        self.center_x = center_x
        self.center_y = center_y
        self.invert_axis_x = invert_axis_x
        self.invert_axis_y = invert_axis_y
        self.plot_margin_top = plot_margin_top
        self.plot_margin_right = plot_margin_right
        self.plot_margin_bottom = plot_margin_bottom
        self.plot_margin_left = plot_margin_left
        self.copy_spacing_x = copy_spacing_x
        self.copy_spacing_y = copy_spacing_y
        self.copy_rotation = copy_rotation
        self.path_smoothness = path_smoothness
        self.path_sort_order = path_sort_order
        self.weed_plot = weed_plot
        self.weed_plot_margin = weed_plot_margin
        self.weed_copy = weed_copy
        self.weed_copy_margin = weed_copy_margin
        self.plot_selected_nodes = plot_selected_nodes

        # Job status flags
        self.changed = True

        # Setting Requirements
        def set_copies(self,n):
            assert n >= 1
            self.copies = n

        def set_scale(self,r):
            assert r > 0
            self.scale = r

        def set_start_position(self,x,y):
            assert x > 0
            assert y > 0
            self.start_x = x
            self.start_y = y

        def set_auto_center(self,enable_x,enable_y):
            assert bool enable_x
            assert bool enable_y
            self.center_x = enable_x
            self.center_y = enable_y

        def set_invert_axis(self,enable_x,enable_y):
            assert bool enable_x
            assert bool enable_y
            self.invert_axis_x = enable_x
            self.invert_axis_y = enable_y

        def set_plot_margin(self,top,right,bottom,left):
            assert top >= 0
            assert right >= 0
            assert bottom >= 0
            assert left >= 0
            self.plot_margin_top = top
            self.plot_margin_right = right
            self.plot_margin_bottom = bottom
            self.plot_margin_left = left

        def set_copy_spacing(self,x,y):
            self.copy_spacing_x = x
            self.copy_spacing_y = y

        def set_path_smoothness(self,s):
            assert s >= .01
            self.path_smoothness = s

        def set_path_sort_order(self,order):
            #assert order in ['One copy at a time']
            self.path_sort_order = order

        def set_weed_plot(self,enabled,margin):
            assert bool enabled
            assert min([self.plot_margin_top,self.plot_margin_right,self.plot_margin_bottom,self.plot_margin_left]) > margin > 0
            self.weed_plot = enabled
            self.weed_plot_margin = margin

        def set_weed_copy(self,enabled,margin):
            assert bool enabled
            assert min([self.plot_margin_top,self.plot_margin_right,self.plot_margin_bottom,self.plot_margin_left]) > margin > 0
            self.weed_copy = enabled
            self.weed_copy_margin = margin
