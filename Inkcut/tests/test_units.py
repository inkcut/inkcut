#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: test_graphic.py
# Author: Copyright 2011 Jairus Martin <frmdstryr@gmail.com>
# Date: 12 July 2011
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
"""Test suite to test the helpers.py unit conversion functions"""
import sys
import os
import logging

dirname = os.path.dirname
THIS_DIR = os.path.join(os.path.abspath(dirname(dirname(__file__))))
TEST_FILE_DIR = os.path.join(THIS_DIR,"tests","input_files")
sys.path.append(THIS_DIR)

from inkcut_lib.helpers import get_unit_value
from inkcut_lib.preferences import UNITS

log = logging.getLogger(__name__)
class TestUnits:
    
    def setUp(self):
        """Setup the Inkcut database and other application settings"""
        self.precision = 8
        pass

    def tearDown(self):
        pass
    
    def test_in_to_default(self):
        """Convert inches to pixels"""
        lhs = get_unit_value("21in")
        rhs = 21*UNITS['length']['in']
        assert lhs == rhs, "%s != %s"%(lhs,rhs)
    
    def test_in_to_uu(self):
        """Convert inches to pixels"""
        lhs = get_unit_value("21in","px")
        rhs = 21*UNITS['length']['in']
        assert lhs == rhs, "%s != %s"%(lhs,rhs)
        
        lhs = get_unit_value("1.328in","px")
        rhs = 1.328*UNITS['length']['in']
        assert lhs == rhs, "%s != %s"%(lhs,rhs)
    
    def test_in_to_mm(self):
        """Convert in to mm"""    
        lhs = round(get_unit_value("1in","mm"),self.precision)
        rhs = 25.4
        assert lhs == rhs, "%s != %s"%(lhs,rhs)
    
    def test_mm_to_in(self):
        """Convert mm to in"""
        lhs = round(get_unit_value("25.4mm","in"),self.precision)
        rhs = 1
        assert lhs == rhs, "%s != %s"%(lhs,rhs)
        
    def test_mm_to_cm(self):
        """Convert mm to cm"""
        lhs = round(get_unit_value("25.4mm","cm"),self.precision)
        rhs = 2.54
        assert lhs == rhs, "%s != %s"%(lhs,rhs)
    
    def test_cm_to_mm(self):
        """Convert cm to mm"""
        lhs = round(get_unit_value("5.08cm","mm"),self.precision)
        rhs = 50.8
        assert lhs == rhs, "%s != %s"%(lhs,rhs)    
        
    def test_mm_to_mm(self):
        """Convert mm to mm"""
        lhs = round(get_unit_value("5.08mm","mm"),self.precision)
        rhs = 5.08
        assert lhs == rhs, "%s != %s"%(lhs,rhs)
        
    def test_MB_to_KB(self):
        """Convert MB to KB"""
        lhs = round(get_unit_value("20MB","KB",'filesize'),self.precision)
        rhs = 20000
        assert lhs == rhs, "%s != %s"%(lhs,rhs)
    
    def test_B_to_MB(self):
        """Convert B to KB"""
        lhs = round(get_unit_value("19992B","MB",'filesize'),self.precision)
        rhs = 0.019992
        assert lhs == rhs, "%s != %s"%(lhs,rhs)    

