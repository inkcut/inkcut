#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: test_plot.py
# Author: Copyright 2011 Jairus Martin <frmdstryr@gmail.com>
# Date: 27 July 2011
#
# License:
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
"""Test suite to test the plot.py file"""
import sys
import os
import logging

dirname = os.path.dirname
sys.path.append(os.path.join(os.path.abspath(dirname(dirname(__file__)))))


from lxml import etree
from lib.plot import Plot
from lib.device import Device

log = logging.getLogger(__name__)

class TestDevice:
    def setUp(self):
        """Setup the Inkcut database and other application settings"""
        pass

    def tearDown(self):
        pass

    def test_get_devices(self):
        """ Test set_copies() and set_rotation(90) should stack along x axis."""
        for device in Device.get_printers():
            print device.name
        assert 1==0
        
    def temp_get_devices_2(self):
        """ Test set_copies() and set_rotation(90) should stack along x axis."""
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        plot.set_copies(4)
        plot.set_rotation(90)
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        
