#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       material.py
#
#       Copyright 2010 Jairus Martin <jrm5555@psu.edu>
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
from sqlalchemy import Table, Column, Integer, Float, String,PickleType
from meta import Base

DEFAULT_PROPERTIES = { # Use this as a schema
    "name":"New Material",#str
    "width":"48.0in",#float + unit
    "length":"36.0in",#float + unit
    "is_roll":True,
    "color":"#FFF",#str
    "cost":"0$",#float per unit
    "margin_top":"0mm",#float + unit
    "margin_left":"0mm",#float + unit
    "margin_right":"0mm",#float + unit
    "margin_bottom":"0mm",#float + unit
    "use_cutting_force":True,
    "cutting_force":"80g",#int with %10 == 0
    "use_cutting_speed":True,
    "cutting_speed":"12cm/s",#int with with %4 == 0
}

class Material(Base):
    """
    Defines material properties for device and size limitations of a job.
    """
    __tablename__ = 'materials'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    cost = Column(Float) # $
    width = Column(Float) # cm
    length = Column(Float) # cm
    margin = Column(PickleType)
    velocity = Column(Integer) # cm/s
    force = Column(Integer) # g
    color = Column(String) # g

    def __init__(self,id=None,name=None,cost=0,width=None,length=None,
            margin=(0,0,0,0),
            velocity=None,force=None,color='#FFF'
            ):
        """
        Create a device instance with it's properties.
        """
        self.id = id
        self.name = name
        self.cost = cost
        self.width = width
        self.length = length
        self.margin = margin
        self.velocity = velocity # usure of units
        self.force = force # grams
        self.color = color # grams

    def get_width(self,in_unit='cm'):
        #return unit(self.width,in_unit)
        pass

    def set_width(self,value,convert_to='cm'):
        #self.width = unit(value,convert_to)
        pass
    
    def get_length(self,in_unit='cm'):
        #return unit(self.length,in_unit)
        pass
    
    def set_length(self,value,convert_to='cm'):
        #self.length = unit(value,convert_to)
        pass
    
    def get_color(self):
        return self.color

    def set_color(self,color):
        assert color.startswith('#')
        assert 3 < len(color) < 8
        self.color = color

