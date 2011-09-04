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

sys.path.append('/usr/share/inkscape/extensions')
import inkex

class InkscapeInkcutPlugin(inkex.Effect):
    def validate(self):
        nodes = self.selected.values()
        for node in nodes:
            tag = node.tag[node.tag.rfind("}")+1:]
            if tag == 'rect':
                inkex.errormsg("A rect object was found in the selection, please convert all objects to paths and try again.\n\nMake sure the statusbar displays only objects of type Path.")
                return False
            elif tag == 'g':
                inkex.errormsg("A group was found in the selection, please ungroup all objects and try again.\n\nMake sure the statusbar displays only objects of type Path.")
                return False
        return True # passed :)

    def effect(self):
        nodes = self.selected
        if self.validate():
            from inkcut import Application
            app = Application()
            if app.load(source=self.document,selected_nodes=nodes):
                app.run()
            
            """
            f = open('/home/rhino/projects/inkcut/app/tmp/inkscape.svg','w+')
            f.write(inkex.etree.tostring(self.document))
            cmd = [sys.executable, '/home/rhino/projects/inkcut/app/main.py']
            cmd.extend(nodes)
            #stdout=open(os.devnull, 'w+')
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, 
            stdout=open(os.devnull, 'w+'), stderr=subprocess.STDOUT,
            close_fds=True)
            p.stdin.write(inkex.etree.tostring(self.document))
            p.stdin.close()
            """




# Create effect instance and apply it.
effect = InkscapeInkcutPlugin()
effect.affect()
