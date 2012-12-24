#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     	InkCut, Plot HPGL directly from Inkscape.
#       hpgl.py
#		hpgl parser
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
def parse(hgpl): # hpgl to polyline # todo, full parsing...
	if type(hpgl) == str:
		hpgl = hpgl.split(';')
	assert type(hpgl)==list, 'hpgl must be a list or string'
	err = []
	poly = []
	pen = ['PU','PD','PR','PD']
	z = True # True == pen is up
	i = 0
	while i < len(hpgl):
		cmd = hpgl[i][:2]
		if cmd == 'PU':
			z = True
		elif cmd == 'PD':
			z = False
		
		if cmd in pen and len(hpgl[i])>2:
			if z:
				c = 'M'
			else:
				c = 'L'
			poly.append([c,map(int,hpgl[i][2:].split(','))])
		else:
			err.append['unsupported command %s'%(cmd)]
			# screw it...
		i+=1
	if len(err):
		return err
	else: # error free
		return poly
		
def format(poly): # polyline to hpgl
	hpgl = []
	line = poly.pop(0) # first is moveto/pen up
	hpgl.append('PU%d,%d'%(map(round,line[1])))
	for line in poly:
		hpgl.append('PD%d,%d'%(map(round,line[1])))
	return hpgl
