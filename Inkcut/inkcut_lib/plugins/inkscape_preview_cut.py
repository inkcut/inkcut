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
		tmp_hpgl = tempfile.NamedTemporaryFile(delete=False,suffix=".hpgl")
		tmp_hpgl.close()
		
		if len(self.selected.values()):
			tmp.write('<svg>')
			for node in self.selected.values():
				tmp.write(inkex.etree.tostring(node))
			tmp.write('</svg>')
		else:
			tmp.write(inkex.etree.tostring(self.document))
		tmp.close()
		
		cmd = [INKCUT,'--convert',tmp.name,tmp_hpgl.name,'--input-type','svg','--output-type','hpgl','--verbose']
		#p = subprocess.call(cmd, stdin=subprocess.PIPE, 
		#	stdout=open(os.devnull, 'w+'), stderr=subprocess.STDOUT,
		#	close_fds=True)
		p = subprocess.call(cmd)
		cmd = [INKCUT,'--convert',tmp_hpgl.name,tmp.name,'--input-type','hpgl','--output-type','svg','--verbose']
		#p = subprocess.call(cmd, stdin=subprocess.PIPE, 
		#	stdout=open(os.devnull, 'w+'), stderr=subprocess.STDOUT,
		#	close_fds=True)
		p = subprocess.call(cmd)
		
		plot = inkex.etree.parse(tmp.name)
		
		os.remove(tmp.name)
		os.remove(tmp_hpgl.name)
        
        svg = self.document.getroot()
        layer = self.getElementById('InkcutPlotPreview') or inkex.etree.SubElement(svg, 'g')
        layer.set('id','InkcutPlotPreview')
        layer.set(inkex.addNS('label', 'inkscape'), 'Inkcut Plot Preview')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        #layer.set('transform', 'translate(0,%s)'%svg.get('height'))
        del layer[:]
		layer.append(plot.getroot())
		#p = subprocess.Popen(cmd, stdin=subprocess.PIPE, 
		#	stdout=open(os.devnull, 'w+'), stderr=subprocess.STDOUT,
		#	close_fds=True)
		#p.stdin.close()
		
	
# Create effect instance and apply it.
effect = InkscapeInkCutPlugin()
effect.affect()
