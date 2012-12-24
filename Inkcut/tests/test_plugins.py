#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: test_plugins.py
# Author: Copyright 2011 Jairus Martin <frmdstryr@gmail.com>
# Date: 12 July 2011
#
# License:
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
"""Test suite to test the plugin.py and hpgl.py files"""
import sys
import os
import logging

dirname = os.path.dirname
sys.path.append(os.path.join(os.path.abspath(dirname(dirname(__file__))),'app'))


from lxml import etree
from inkcut_lib.graphic import Graphic
from inkcut_lib.plugin import Plugin,path_is_closed
from inkcut_lib.hpgl import hpgl as HPGL

log = logging.getLogger(__name__)
class TestPlugins:
    def setUp(self):
        pass
        
    def tearDown(self):
        pass

    def test_apply_cutting_overlap(self):
        """Test Plugin.apply_cutting_overlap()!"""
        overlap = 20
        plugin = Plugin()
        g = Graphic(os.path.join(dirname,"arrow.svg"))
        g.set_scale(HPGL.HPGL_SCALE,HPGL.HPGL_SCALE)
        paths = g.get_polyline()
        lengths = []
        for path in paths:
            lengths.append(g.get_path_length(path=path))
        
        plugin.apply_cutting_overlap(paths,overlap)
        for path,length in zip(paths,lengths):
            if path_is_closed(path):
                new_length = g.get_path_length(path=path)
                assert round(length+overlap,10) == round(new_length,10), "%s != %s" % (round(length+overlap,10),round(new_length,10))
            else:
                assert round(length,10) == round(new_length,10), "%s != %s" % (round(length,10),round(new_length,10))

    def test_hpgl_export_plugin(self):
        """Test that HPGL.Export() works! """
        plugin = inkcut_plugin(HPGL.Export())
        plugin.run()
        f = open("out/%s.hpgl"%sys._getframe().f_code.co_name,"w")
        f.write(plugin.output)
        f.close()

    def test_hpgl_import_plugin(self):
        """Test that HPGL.Import() works! """
        
        plugin = inkcut_plugin(HPGL.Import())
        plugin.input = "out/test_hpgl_export_plugin.hpgl"
        plugin.run()
        f = open("out/%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plugin.output)
        f.close()

        

    
def inkcut_plugin(plugin):
    """What the Inkcut plugin handler will call when using plugins."""
    if plugin.mode.lower() == "export":
        # Populate export values
        plugin.input = os.path.join(os.path.abspath(os.path.dirname(__name__)), os.path.join(dirname,"arrow.svg"))
        plugin.export_init(plot={},device={'cutting_overlap':(10,False)})
        return plugin
    elif plugin.mode.lower() == "import":
        # Populate import values
        return plugin
    else:
        raise ValueError("plugin.mode must be either \"import\" or \"export\" (case insensative)")
