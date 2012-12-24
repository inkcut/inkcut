#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     	InkCut, Plot HPGL directly from Inkscape.
#       hpgl.py
#		functions to send finished data to plotter/cutter
#       
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
#
import sys
sys.path.append('/usr/share/inkscape/extensions')
import cubicsuperpath, simplepath, cspsubdiv, simpletransform,bezmisc,copy,math
from simpletransform import *
from lxml import etree
import inkex

def svg(plot): # quick way to preview what it will look like... idk if it's as useful
	#create a preview svg
	plot = copy.deepcopy(plot)
	svg = etree.Element(inkex.addNS('svg','svg'))
	svg.set('height',str(plot.dimensions[1]))
	svg.set('width',str(plot.getSize()[0]))
	svg.set('version','1.1')
	style = {'fill' : '#20CE39','fill-opacity': '.8','stroke':'#116AAB'}
	style = simplestyle.formatStyle(style)
	for clone in plot.createTiledClones():
		clone.mirrorYAxis()
		for path in clone.paths:
			p = inkex.etree.Element(inkex.addNS('path','svg'))
			p.set('style', style)
			path.translatePath(0,plot.size[1])
			p.set('d',simplepath.formatPath(path.data))
			svg.append(p)
		
	return svg

def hpgl(plot):
	#create a preview svg
	svg = etree.Element(inkex.addNS('svg','svg'))
	svg.set('height',str(plot.dimensions[1]))
	svg.set('width',str(plot.getSize()[0]+plot.startPosition[0]+plot.finishPosition[0]))
	svg.set('version','1.1')
	"""
	bg = inkex.etree.Element(inkex.addNS('rect','svg'))
	style = {'fill' : 'none','stroke-opacity': '.8','stroke':'#212425','stroke-width':'10'}
	bg.set('style', simplestyle.formatStyle(style))
	bg.set('x','0')
	bg.set('y','0')
	bg.set('width',str(plot.dimensions[0]))
	bg.set('height',svg.get('height'))
	svg.append(bg)
	"""
	spPU = [['M',[0,0]]]
	spPD = []
	for c in plot.toHPGL().split(';'):
		if c[:2] == "PU":
			p = map(int,c[2:].split(','))
			spPD.append(['M',p])
			spPU.append(['L',p])
		elif c[:2] == "PD":
			p = map(int,c[2:].split(','))
			spPU.append(['M',p])
			spPD.append(['L',p])		
	
	pu = inkex.etree.Element(inkex.addNS('path','svg'))
	
	simplepath.scalePath(spPU,0.088582677,-0.088582677)
	simplepath.translatePath(spPU,0,float(svg.get('height')))
	
	style = {'fill' : 'none','stroke-opacity': '.8','stroke':'#116AAB'}
	pu.set('style', simplestyle.formatStyle(style))
	pu.set('d',simplepath.formatPath(spPU))
	
	
	pd = inkex.etree.Element(inkex.addNS('path','svg'))
	
	style = {'fill' : 'none','stroke-opacity': '.8','stroke':'#AB3011'}
	pd.set('style', simplestyle.formatStyle(style))
	pd.set('d',simplepath.formatPath(spPD))
	
	# Connect elements together.
	svg.append(pu)
	svg.append(pd)
	return svg


def inkscape(hpgl,svg,inkex):
	layer = inkex.etree.SubElement(svg, 'g')
	layer.set(inkex.addNS('label', 'inkscape'), 'InkCut Preview Layer')
	layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
	spPU = [['M',[0,0]]]
	spPD = []
	for c in hpgl.split(';'):
		if c[:2] == "PU":
			p = map(int,c[2:].split(','))
			spPD.append(['M',p])
			spPU.append(['L',p])
		elif c[:2] == "PD":
			p = map(int,c[2:].split(','))
			spPU.append(['M',p])
			spPD.append(['L',p])		
	
	pu = inkex.etree.Element(inkex.addNS('path','svg'))
	
	simplepath.scalePath(spPU,0.088582677,-0.088582677)
	simplepath.translatePath(spPU,0,float(svg.get('height')))
	
	style = {'fill' : 'none','stroke-opacity': '.8','stroke':'#116AAB'}
	pu.set('style', simplestyle.formatStyle(style))
	pu.set('d',simplepath.formatPath(spPU))
	
	
	pd = inkex.etree.Element(inkex.addNS('path','svg'))
	
	style = {'fill' : 'none','stroke-opacity': '.8','stroke':'#AB3011'}
	pd.set('style', simplestyle.formatStyle(style))
	pd.set('d',simplepath.formatPath(spPD))
	
	# Connect elements together.
	layer.append(pu)
	layer.append(pd)

