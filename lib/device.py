#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       device.py
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
import platform
import os
from unit import unit
from sqlalchemy import Table, Column, Integer, Float, Unicode,Boolean,PickleType
from meta import Base

if platform.system() == 'Linux':
    import cups            
elif platform.system() == 'Windows':
    pass
        

class Device(Base):
    """
    Interface to communcate with a plotter or cutter as well as get
    properties such as width, length, speed, status etc.
    Does final job svg to hpgl conversion.
    """
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    brand = Column(Unicode)
    model = Column(Unicode)
    operating_cost = Column(Float)

    width = Column(Float)
    length = Column(Float)
    uses_media_roll = Column(Boolean)
    margin = Column(PickleType)
    blade_offset = Column(Float)
    blade_overcut = Column(Float)
    calibration_scale = Column(PickleType) # (float,float)

    command_language = Column(Unicode)

    velocity_enable = Column(Boolean,default=False)
    velocity_min = Column(Integer)
    velocity_max = Column(Integer)
    velocity = Column(Integer)

    force_enable = Column(Boolean,default=False)
    force_min = Column(Integer)
    force_max = Column(Integer)
    force = Column(Integer)




    def __init__(self,id=None,name=None,brand=None,model=None,
            operating_cost=0,width=None,length=None,
            uses_media_roll=True,
            margin=[0,0,0,0],
            blade_offset=unit(.25,'mm'),
            blade_overcut=unit(2,'mm'),
            calibration_scale=(1,1),command_language='HPGL',
            velocity_enable=False,velocity_min=None,
            velocity_max=None,velocity=None,
            force_enable=False,force_min=None,
            force_max=None,force=None,
        ):
        """
        Create a device instance with it's properties.
        """
        self.id = id
        self.name = name
        self.brand = brand
        self.model = model
        self.operating_cost = operating_cost

        self.width = width
        self.length = length
        self.uses_media_roll = uses_media_roll
        self.margin = margin
        self.blade_offset = blade_offset
        self.blade_overcut = blade_overcut
        self.calibration = calibration_scale

        self.command_language = command_language
        self.velocity_enable = velocity_enable
        self.velocity_min = velocity_min
        self.velocity_max = velocity_max
        self.velocity = velocity

        self.force_enable = force_enable
        self.force_min = force_min
        self.force_max = force_max
        self.force = force

    @staticmethod
    def get_printers():
        """Returns a list of printers installed on the system."""
        if platform.system() == 'Linux':
            con = cups.Connection()
            printers = []
            for printer in con.getPrinters():
                printers.append(Device(name=printer))
            return printers
            
        elif platform.system() == 'Windows':
            return []

    @staticmethod
    def get_printer_by_name(name):
        """Returns a list of printers installed on the system."""
        for printer in Device.get_printers():
            if printer.name == name:
                return printer
        

    @staticmethod
    def port_scan():
        """scan for available ports. return a list of tuples (num, name)"""
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append( (i, s.portstr))
                s.close()   # explicit close 'cause of delayed GC in java
            except serial.SerialException:
                pass
        return available

    # Device output
    def submit(self,data):
        """ General interface for sending data to the device """
        self._write_to_printer(data)

    def _write_to_printer(self,data):
        """
        This send the hpgl data to a printer, using cups for linux.
        """
        if platform.system() == 'Linux':
            printer = os.popen('lpr -P %s'%(self.name),'w')
            #TODO: Insert buffer here...
            printer.write(data)
            printer.close()
            
        elif platform.system() == 'Windows':
            pass
            # pywin32 or something here...
        

    def _write_to_serial(self):
        """
        This sends the hpgl data to a serial port using pyserial.
        """
        pass

    def __repr__(self):
        return "<Device('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s''%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')>" % (
                self.id,
                self.name,
                self.brand,
                self.model,
                self.operating_cost,
                self.width,
                self.length,
                self.uses_media_roll,
                self.margin,
                self.blade_offset,
                self.blade_overcut,
                self.calibration_scale,
                self.command_language,
                self.velocity_enable,
                self.velocity_min,
                self.velocity_max,
                self.velocity,
                self.force_enable,
                self.force_min,
                self.force_max,
                self.force
            )

