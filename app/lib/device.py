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
import serial
from unit import unit
from sqlalchemy import Table, Column, Integer, Float, Unicode,Boolean
from meta import Base

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
    margin_top = Column(Float)
    margin_right = Column(Float)
    margin_bottom = Column(Float)
    margin_left = Column(Float)
    blade_offset = Column(Float)
    blade_overcut = Column(Float)
    calibration_x = Column(Float)
    calibration_y = Column(Float)

    command_language = Column(Unicode)
    command_buffer = Column(Integer)
    command_method = Column(Unicode)

    command_port = Column(Unicode)
    command_baudrate = Column(Integer)
    command_parity = Column(Unicode)
    command_stopbits = Column(Float)
    command_bytesize = Column(Integer)
    command_xonxoff = Column(Boolean)
    command_rtscts = Column(Boolean)
    command_dsrdtr = Column(Boolean)

    command_use_software = Column(Boolean,default=False)
    velocity_min = Column(Integer)
    velocity_max = Column(Integer)
    velocity = Column(Integer)
    force_min = Column(Integer)
    force_max = Column(Integer)
    force = Column(Integer)




    def __init__(self,id=None,name=None,brand=None,model=None,
            operating_cost=0,width=None,length=None,
            uses_media_roll=True,
            margin_top=0,margin_right=0,margin_bottom=0,margin_left=0,
            blade_offset=unit(.25,'mm'),
            blade_overcut=unit(2,'mm'),
            calibration_x=1,calibration_y=1,command_language='HPGL',
            command_buffer=8,command_method=None,command_port=None,
            command_baudrate=9600,command_parity='None',
            command_stopbits=1,command_bytesize=8,command_xonxoff=False,
            command_rtscts=False,command_dsrdtr=False,
            command_use_software=False,velocity_min=None,
            velocity_max=None,velocity=None,force_min=None,
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
        self.margin_top = margin_top
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom
        self.margin_left = margin_left
        self.blade_offset = blade_offset
        self.blade_overcut = blade_overcut
        self.calibration_x = calibration_x
        self.calibration_y = calibration_y

        self.command_language = command_language
        self.command_buffer = command_buffer
        self.command_method = command_method

        self.command_port = command_port
        self.command_baudrate = command_baudrate
        self.command_parity = command_parity
        self.command_stopbits = command_stopbits
        self.command_bytesize = command_bytesize
        self.command_xonxoff = command_xonxoff
        self.command_rtscts = command_rtscts
        self.command_dsrdtr = command_dsrdtr

        self.command_use_software = command_use_software
        self.velocity_min = velocity_min
        self.velocity_max = velocity_max
        self.velocity = velocity
        self.force_min = force_min
        self.force_max = force_max
        self.force = force

    # Device status
    def status():
        """
        What the device is doing, what state, connection, processing...
        """
        pass

    def _connect():
        """Connect to the device, update status"""
        pass

    def _disconnect():
        """Disconnect the device, update status"""
        pass

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

    def process(self,data):
        """
        Processes data before final output, adjusts for blade offset,
        velocity, and any other device specific settings
        """
        pass

    # Device output
    def submit(self,data):
        """ General interface for sending data to the device """
        pass

    def _write_to_printer(self,printer):
        """
        This send the hpgl data to a printer, using cups for linux.
        """
        pass

    def _write_to_serial(self):
        """
        This sends the hpgl data to a serial port using pyserial.
        """
        pass

    def __repr__(self):
        return "<Device('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s''%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s''%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')>" % (
                self.id,
                self.name,
                self.brand,
                self.model,
                self.operating_cost,
                self.width,
                self.length,
                self.uses_media_roll,
                self.margin_top,
                self.margin_right,
                self.margin_bottom,
                self.margin_left,
                self.blade_offset,
                self.blade_overcut,
                self.calibration_x,
                self.calibration_y,
                self.command_language,
                self.command_buffer,
                self.command_method,
                self.command_port,
                self.command_baudrate,
                self.command_parity,
                self.command_stopbits,
                self.command_bytesize,
                self.command_xonxoff,
                self.command_rtscts,
                self.command_dsrdtr,
                self.command_use_software,
                self.velocity_min,
                self.velocity_max,
                self.velocity,
                self.force_min,
                self.force_max,
                self.force
            )

