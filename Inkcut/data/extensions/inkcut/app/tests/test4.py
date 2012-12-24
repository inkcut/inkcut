#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       name.py
#-----------------------------------------------------------------------
#       Copyright 2010 Jairus Martin <frmdstryr@gmail.com>
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
#-----------------------------------------------------------------------
import sys
sys.path.append('/home/rhino/projects/inkcut/app/bin')
import path
from pprint import pprint
import cubicsuperpath, simplepath, cspsubdiv, simpletransform,bezmisc,copy,math

from lxml import etree
drawing = etree.parse('/home/rhino/projects/inkcut/app/tmp/drawing.svg').getroot()

def getSelectedById(IDlist,drawing): # returns lxml elements that have an id in IDlist in the svg
	ele=[]
	for e in drawing.iterfind('.//*[@id]'):
		if e.get('id') in IDlist:
			ele.append(e)
	return ele

#paths = ['r','ellipse','hexagon','spiro','curvypath','hline','vline','roundedbox','pie']	
paths = ['r']
nodes = getSelectedById(paths,drawing)



plot = path.Plot({'offset':.25})
plot.loadGraphic(nodes)
plot.setCopies(1)
pprint(plot.toHPGL())
"""
g = plot.graphic
g.mirrorYAxis()
print g.mirror
for node in nodes:
	pprint(node.get('id'))
#print plot.data
p = g.paths[0]
#pprint(plot.data)
pprint(p.data)
pprint(p.toHPGL())
#p.setOvercut(200)
#pprint(p.toPolyline(.2))

"""


"""
plot = path.Plot(g)
plot.setSmoothness(.1)
plot.setScale(11.288888889)



p = path.Path(g.data[0])
pprint(p.data)

#pprint(p.toPolyline(.0097))
hpgl = plot.toHPGL()
print hpgl
print len(hpgl.split(';'))

#p.setOvercut('.01')
#pprint(p.data)

#pprint(p.data)
"""




