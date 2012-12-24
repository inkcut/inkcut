# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2011 Jairus Martin - Vinylmark LLC <jrm@vinylmark.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE
import math

precision = 6
def subtract(p2,p1):
    """ Returns p2-p1 """
    return [p2[0]-p1[0],p2[1]-p1[1]]

def add(p1,p2):
    """ Returns p2+p1 """
    return [p2[0]+p1[0],p2[1]+p1[1]]

def point_distance((x1,y1),(x2,y2)):
    """ Returns the distance between two points as a float. """
    from math import sqrt
    return sqrt((y2-y1)**2+(x2-x1)**2)

def line_t_point((x1,y1),(x2,y2),t):
    """ Returns the position at a time between a parametric line. """
    return (x1+t*(x2-x1),y1+t*(y2-y1))

def qubic_bezier_t_point((x1,y1),(x2,y2),t):
    """ Returns the position at a time between a parametric line. """
    return (x1+t*(x2-x1),y1+t*(y2-y1))
    
def dot(p0,p1):
    p = 0
    for a1,a2 in zip(p0,p1):
        p +=a1*a2
    return p				

def norm(p0):
    n = 0
    for a in p0:
        n +=a*a
    return math.sqrt(n)

def point_equal(p1,p2):
    return round(p1[0],6)==round(p2[0],precision) and round(p1[1],6)==round(p2[1],precision)

def angle_between(v1,v2):
    assert norm(v1) > 0 and norm(v2) > 0, "Invalid vectors"
    r = round(dot(v1,v2)/(norm(v1)*norm(v2)),precision)
    return math.acos(r)
