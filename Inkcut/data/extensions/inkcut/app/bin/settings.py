#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     	InkCut, Plot HPGL directly from Inkscape.
#       settings.py
#		application settings
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
import gtk

class Settings:
	def __init__(self,filename,widgets):
		self.filename = filename
		self.xml = etree.parse(filename).getroot()
		self.gui = widgets

	def load(self,id):
		s = self.xml.find('setting[@id="%s"]'%id)
		err = []
		if len(s):
			app = s.find('app')
			for item in app:
				try:
					widget = self.gui[item.get('id')]
					t = type(widget)
					if t == gtk.RadioButton or t == gtk.CheckButton:
						widget.set_active(item.get('val')=="true")
					elif t == gtk.Adjustment:
						widget.set_value(float(item.get('val')))
					elif t==gtk.ComboBox or t==gtk.ComboBoxEntry: # will not load custom
						widget.set_active(int(item.get('val')))
					else:
						err.append("unknown type %s for item %s"%(t,item.get('id')))
				except:
					err.append("error loading: %s"%(item.get('id')))
			if not len(err):
				return True
		
		return err
		

	def save(self,id):
		# check if id exists
		s = self.xml.find('setting[@id="%s"]'%id)
		err = []
		# delete if exists?
		if len(s):
			del s[0]
		else:
			s = etree.SubElement(self.xml,'setting')
			s.set('id',id)
			
		app = etree.SubElement(s,'app')
		
		# add the items
		for id,widget in self.gui.iteritems():
			t = type(widget)
			item = etree.SubElement(app,'item')
			item.set('id',id)
			if t == gtk.RadioButton or t == gtk.CheckButton:
				if widget.get_active():
					item.set('val','true')
				else:
					item.set('val','false')
			elif t == gtk.Adjustment:
				item.set('val',str(widget.get_value()))
			elif t==gtk.ComboBox or t==gtk.ComboBoxEntry: # will not load custom
				item.set('val',str(widget.get_active()))
			else:
				err.append("unknown type %s for item %s"%(t,item.get('id')))
		
		f = open(self.filename,'w+')
		f.write(etree.tostring(self.xml, pretty_print=True)) # doesnt pprint...
		f.close()
		if not len(err):
			return True
		else:
			return err
