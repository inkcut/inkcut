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
import tempfile

sys.path.append('/usr/share/inkscape/extensions')
sys.path.append('/media/Storage/Projects/inkcut/inkcut/inkcut_lib')
import inkex
INKCUT = '/media/Storage/Projects/inkcut/bin/inkcut'

class InkscapeInkCutPlugin(inkex.Effect):
		
	def effect(self):
		tmp = tempfile.NamedTemporaryFile(delete=False,suffix=".svg")
		if len(self.selected.values()):
			tmp.write('<svg>')
			for node in self.selected.values():
				tmp.write(inkex.etree.tostring(node))
			tmp.write('</svg>')
		else:
			doc = self.document
			tmp.write(inkex.etree.tostring(doc))
		tmp.close()
		
		cmd = [INKCUT,'--plot',tmp.name,'--plugin','inkscape','--input-type','svg','--verbose']
		p = subprocess.Popen(cmd)
		#p = subprocess.Popen(cmd, stdin=subprocess.PIPE, 
		#	stdout=open(os.devnull, 'w+'), stderr=subprocess.STDOUT,
		#	close_fds=True)
		#p.stdin.close()
		
	
# Create effect instance and apply it.
effect = InkscapeInkCutPlugin()
effect.affect()
