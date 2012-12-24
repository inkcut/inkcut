#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#		 InkCut, Plot HPGL directly from Inkscape.
#	   extension.py
#	   
#	   Copyright 2010 Jairus Martin <frmdstryr@gmail.com>
#	   
#	   This program is free software; you can redistribute it and/or modify
#	   it under the terms of the GNU General Public License as published by
#	   the Free Software Foundation; either version 2 of the License, or
#	   (at your option) any later version.
#	   
#	   This program is distributed in the hope that it will be useful,
#	   but WITHOUT ANY WARRANTY; without even the implied warranty of
#	   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	   GNU General Public License for more details.
#	   
#	   You should have received a copy of the GNU General Public License
#	   along with this program; if not, write to the Free Software
#	   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#	   MA 02110-1301, USA.
#
import sys
import subprocess
import os
import tempfile

sys.path.append('/usr/share/inkscape/extensions')
sys.path.append('/media/Storage/Projects/inkcut/inkcut/inkcut_lib')
import inkex
from helpers import get_selected_nodes

class InkscapeInkCutPlugin(inkex.Effect):
	def __init__(self):
		# Call the base class constructor.
		inkex.Effect.__init__(self)
		"""
		# Define output options
		self.OptionParser.add_option('-s', action = 'store',
		  type = 'string', dest = 'dialog',
		  help = 'Args to send to inkcut.')
		"""
		
	def effect(self):
		svg = len(self.selected) and get_selected_nodes(self.document,self.selected) or self.document
		tmp = tempfile.NamedTemporaryFile(delete=False)
		tmp.write(inkex.etree.tostring(svg))
		tmp.close()
		cmd = ['/media/Storage/Projects/inkcut/bin/inkcut','-p',tmp.name,'--remove']
		stdout=open(os.devnull, 'w+')
		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, 
			stdout=open(os.devnull, 'w+'), stderr=subprocess.STDOUT,
			close_fds=True)
		p.stdin.close()
		
			
			
		
# Create effect instance and apply it.
effect = InkscapeInkCutPlugin()
effect.affect()
