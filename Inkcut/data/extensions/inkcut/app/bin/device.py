#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     	InkCut, Plot HPGL directly from Inkscape.
#       device.py
#		device settings
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
import serial
from lxml import etree
import cups
import os

class Device:
	def __init__(self,config={}):
		#self.xml = etree.parse(filename).getroot()
		conf = {'width':0,'length':0,'name':'','interface':'serial','serial':{'port':'/dev/ttyUSB0','baud':9600}}
		conf.update(config)
		self.width = conf['width']
		self.length = conf['length']
		self.name = conf['name']
		self.interface = conf['interface']
		self.serial = conf['serial']
		
	
	def getPrinters(self):
		con = cups.Connection()
		printers = con.getPrinters()
		self.printers = printers
	
	def save(self,id,attribs): # save settings to xml
		dev = self.xml.find('device[@id="%s"]'%id)
		err = []
		# delete if exists?
		if len(dev):
			del dev[0]
		else:
			dev = etree.SubElement(self.xml,'device')
			dev.set('id',id)
		iface = etree.SubElement(d, "interface")
		for key,value in attribs.iteritems():
			iface.set(key,value)
			


	def plot(self,filename):
		def toSerial(data,settings):
			assert type(data) == str, "input data must be a str type"
			import serial

			# set default settings
			set = {'baud':9600}
			set.update(settings);
			
			#create serial and set settings
			ser = serial.Serial()
			ser.baudrate = set['baud']
			ser.port = set['port']
			ser.open()
			if ser.isOpen():
				#send data & return bits sent
				bits = ser.write(data);
				ser.close();		
				return True;
			else:
				return False;

		def toPrinter(data,printer):
			assert type(data) == str, "input data must be a str type"
			assert type(printer) == str, "printer name must be a string"
			
			printer = os.popen('lpr -P %s'%(printer),'w')
			printer.write(data)
			printer.close()
			return True;
		
		
		f=open(filename,'r')
		if self.interface=='printer':
			toPrinter(f.read(),self.name)
		elif self.interface=='serial':
			toSerial(f.read(),self.serial)
		else:
			raise AssertionError('Invalid interface type, only printers and serial connections are supported.')
		

	

