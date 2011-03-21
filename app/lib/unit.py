#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       unit.py
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

# according to svg 1.1 specification http://www.w3.org/TR/SVG/coords.html
UNIT = {
    'in':90.0,
    'pt':1.25,
    'px':1,
    'mm':3.5433070866,
    'cm':35.433070866,
    'm':3543.3070866,
    'km':3543307.0866,
    'pc':15.0,
    'yd':3240.0,
    'ft':1080.0
}

SCALE = {

}

def unit(x,convert_to="px",from_unit="px"):
    """
    Converts a number in px to given units.
    Pass a third unit to convert from that unit to unit.
    """
    assert convert_to in UNIT, "Cannot convert to unknown unit: %s" % convert_to
    assert from_unit in UNIT, "Cannot from unknown unit: %s" % from_unit
    return x*UNIT[convert_to]/UNIT[from_unit]
