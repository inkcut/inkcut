#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       job.py
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
from unit import unit
from sqlalchemy import Table, Column, Integer, Float, String
from meta import Base

class Material(Base):
    """
    Defines material properties for device and size limitations of a job.
    """
    __tablename__ = 'materials'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    cost = Column(Float)
    width = Column(Float)
    length = Column(Float)
    margin_top = Column(Float)
    margin_right = Column(Float)
    margin_bottom = Column(Float)
    margin_left = Column(Float)
    velocity = Column(Integer)
    force = Column(Integer)
    
    def __init__(self,id=None,name=None,cost=0,width=None,length=0,
            margin_top=0,margin_right=0,margin_bottom=0,margin_left=0,
            velocity=None,force=None
            ):
        """
        Create a device instance with it's properties.
        """
        self.id = id
        self.name = name
        self.cost = cost
        self.width = width
        self.length = length
        self.margin_top = margin_top
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.velocity = velocity # usure of units
        self.force = force # grams
 
    def __repr__(self):
        return "<Material('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')>" % (
                self.id,self.name,self.cost,self.width,self.length,
                self.margin_top,self.margin_right,self.margin_bottom,
                self.margin_left,self.velocity,self.force
            )


