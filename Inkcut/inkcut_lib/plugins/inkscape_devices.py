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
import sys
import subprocess
import os

sys.path.append('/usr/share/inkscape/extensions')
import inkex

INKCUT = '/media/Storage/Projects/inkcut/bin/inkcut'

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
		cmd = [INKCUT,'--show-dialog','DeviceProperties']
		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, 
			stdout=open(os.devnull, 'w+'), stderr=subprocess.STDOUT,
			close_fds=True)
		p.stdin.close()
		
# Create effect instance and apply it.
effect = InkscapeInkCutPlugin()
effect.affect()
