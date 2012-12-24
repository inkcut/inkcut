#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     	InkCut, Plot HPGL directly from Inkscape.
#       material.py
#		loading materials
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

from lxml import etree

def getSize(name,xml='/home/rhino/projects/inkcut/app/config/materials.xml'):
	xml = etree.parse(xml).getroot()
	m = xml.find('material[@name="%s"]'%name)
	return (float(m.get('w')),float(m.get('l')))
	
