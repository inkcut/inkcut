#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       path.py
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

class GraphicLanguage(object):
    """
    Common API for different graphic languages: HPGL, GPGL, DMPL, Postscript
    """

    def __init__(self):
        """
        Create a device instance with it's properties.
        """
        self.id = None
        self.name = None
        self.status = "Offline"
        self.command_set = "HPGL"
        self.buffer = 8
        self.dimensions = [0,0,0] # maximum x,y,z dimensions set 0 for infinit
        self.velocity = 4 # usure of units
        self.blade_offset = unit(.25,'mm')


    def _send_to_printer(self,printer):
        """
        This send the hpgl data to a printer, using cups for linux.
        """
        pass

    def _send_to_serial(self,port,baud=9600):
        """
        This sends the hpgl data to a serial port using pyserial.
        """
        pass




