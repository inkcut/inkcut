#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: test_plot.py
# Author: Copyright 2011 Jairus Martin <frmdstryr@gmail.com>
# Date: 27 July 2011
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
"""Test suite to test the plot.py file"""
import sys
import os
import logging

dirname = os.path.dirname
sys.path.append(os.path.join(os.path.abspath(dirname(dirname(__file__))),'app'))
import inkcut

from lxml import etree

from lib.plot import Plot

log = logging.getLogger(__name__)
class TestPlot:
    def setUp(self):
        """Setup the Inkcut database and other application settings"""
        pass

    def tearDown(self):
        pass

    def test_plot_area(self):
        """
        Test the get_available_width() and get_available_height() functions.
        They should return the material width and height minus the padding
        around the outside.
        """
        plot = Plot(90*12,90*12*4)
        plot.set_padding(35,0,35,0) # should be default but to make sure
        assert plot.get_available_width() == 90*12
        assert plot.get_available_height() == 90*12*4-70

    def test_set_padding(self):
        """ Test the set_padding() """
        plot = Plot(90*12,90*12*4)
        plot.set_padding(35,0,35,0)
        assert plot.get_available_width() == 90*12
        assert plot.get_available_height() == 90*12*4-70
        plot.set_padding(top=30)
        assert plot.get_available_width() == 90*12
        assert plot.get_available_height() == 90*12*4-65
        plot.set_padding(right=30)
        assert plot.get_available_width() == 90*12-30
        assert plot.get_available_height() == 90*12*4-65
        plot.set_padding(left=17.3)
        assert plot.get_available_width() == 90*12-30-17.3
        assert plot.get_available_height() == 90*12*4-65
        plot.set_padding(bottom=0)
        assert plot.get_available_width() == 90*12-30-17.3
        assert plot.get_available_height() == 90*12*4-30
        plot.set_padding(top=35,right=0,bottom=35,left=0)
        assert plot.get_available_width() == 90*12
        assert plot.get_available_height() == 90*12*4-70
        plot.set_padding(top=0,right=0,bottom=0,left=0)
        assert plot.get_available_width() == 90*12
        assert plot.get_available_height() == 90*12*4

    def test_set_graphic(self):
        """ Test set_graphic() and get_preview_xml() """
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        assert plot.get_width() == plot.graphic.get_width()
        assert round(plot.get_height(),10) == round(plot.graphic.get_height(),10) # why does it need rounding???

    def test_set_graphic_2(self):
        """ Test set_graphic() and setting a new graphic after one has already been set. """
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        f = open("out/plot_%s_1.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        assert plot.get_width() == plot.graphic.get_width()
        assert round(plot.get_height(),10) == round(plot.graphic.get_height(),10) # why does it need rounding???
        plot.set_graphic(etree.tostring(etree.parse("fat-giraffes.svg")))
        f = open("out/plot_%s_2.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        assert round(plot.get_width(),10) == round(plot.graphic.get_width(),10)
        assert round(plot.get_height(),10) == round(plot.graphic.get_height(),10) # why does it need rounding???

    def test_set_position(self):
        """ Test set_position()"""
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        log.info("Checking position 0,0...")
        assert map(lambda x:round(x,10),plot.get_position()) == [0,0], "Got %s" % map(lambda x:round(x,10),plot.get_position())
        log.info("OK")
        log.info("Checking position 50,0...")
        plot.set_position(50,0)
        assert map(lambda x:round(x,10),plot.get_position()) == [50,0], "Got %s" % map(lambda x:round(x,10),plot.get_position())
        log.info("OK")
        log.info("Checking position 13.2,459...")
        plot.set_position(13.2,459)
        assert map(lambda x:round(x,10),plot.get_position()) == [13.2,459], "Got %s" % map(lambda x:round(x,10),plot.get_position())
        log.info("OK")
        f = open("out/plot_%s_1.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()


    def test_set_copies(self):
        """ Test set_copies() and set_rotation(90) should stack along x axis."""
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        plot.set_copies(4)
        plot.set_rotation(90)
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        spacing = plot.get_spacing()
        assert len(plot._data) == 4
        assert plot.get_width() == plot.graphic.get_width()
        assert round(plot.get_height(),10) == round(plot.graphic.get_height()*4+spacing[1]*3,10)

    def test_set_copies_2(self):
        """ Test set_copies(7) with no rotation should stack along y axis."""
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        plot.set_copies(7) # two horizontal stacks and one extra
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        spacing = plot.get_spacing()
        assert len(plot._data) == 7
        assert plot.get_stack_size_x() == 3, "Stack size: %s" % plot.get_stack_size_x()
        assert round(plot.get_width(),10) == round(plot.graphic.get_width()*3 + spacing[0]*2,10)
        assert round(plot.get_height(),10) == round(plot.graphic.get_height()*3+spacing[1]*2,10)

    def test_set_copies_3(self):
        """ Test set_copies() and get_preview_xml() should stack 7 along  the x axis. """
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        plot.set_copies(7)
        plot.set_rotation(90)
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        spacing = plot.get_spacing()
        assert len(plot._data) == 7
        assert plot.get_stack_size_y() == 5, "Stack size: %s" % plot.get_stack_size_y()
        assert round(plot.get_width(),10) == round(plot.graphic.get_width()*2 + spacing[0],10)
        assert round(plot.get_height(),10) == round(plot.graphic.get_height()*5+spacing[1]*4,10)

    def test_graphic_rotation(self):
        """ Test that the graphic is rotated and plot automatically updated. """
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.parse("arrow.svg"))
        h = plot.graphic.get_height()
        w = plot.graphic.get_width()
        plot.graphic.set_rotation(90)
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        spacing = plot.get_spacing()
        assert round(plot.get_width(),10) == round(h,10), "they should be rotated"
        assert round(plot.get_height(),10) == round(w,10)

    def test_material_size_limited(self):
        """Test that the material is sized correctly when limited=True"""
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.parse("arrow.svg"))
        plot.set_padding(35,0,35,0)
        h = 170.563
        log.debug(" %s should = %s" %(round(plot.get_material_height(limited=True),3),h+70))
        assert round(plot.get_material_height(limited=True),3) == h+70
        w = 333.469
        log.debug(" %s should = %s" %(round(plot.get_material_width(limited=True),3),w))
        assert round(plot.get_material_width(limited=True),3) == w

    def test_weedline(self):
        """
        Test that a weedline graphic is added to the plot and that 0 padding
        doesn't change the bbox.
        """
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        plot.set_rotation(90)
        plot.set_copies(7)
        bbox = plot.get_bounding_box()
        plot.set_weedline(True)
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        assert len(plot._data) == 8, "len(plot._data) = %s, expect 8" %(len(plot._data))
        assert map(lambda x: round(x,10),plot.get_bounding_box()) == map(lambda x: round(x,10),bbox), "bbox before %s != bbox after weedline %s" % (bbox,plot.get_bounding_box())

    def test_weedline_padding(self):
        """
        Test that a weedline graphic is added to the plot and that 35 padding
        only changes the width and height of the bbox by +=2*padding.
        """
        plot = Plot(90*12,90*12*4)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        plot.set_rotation(90)
        plot.set_copies(6)
        bbox = plot.get_bounding_box()
        plot.set_weedline(True)
        pad = 35
        plot.set_weedline_padding(pad)
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        assert len(plot._data) == 7, "len(plot._data) = %s, expect 7" %(len(plot._data))
        assert map(lambda x: round(x,10),plot.get_bounding_box()) == [0,bbox[1]+2*pad,35,bbox[3]+2*pad], "bbox before %s != bbox after weedline %s" % ([0,bbox[1]+35,35,bbox[3]+35],map(lambda x: round(x,10),plot.get_bounding_box()))



    def test_align_center_x(self):
        """ Makes sure the graphic is centered correctly in the x direction"""
        plot = Plot(90*12,90*12*4)
        plot.set_padding(35,0,35,0)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        plot.set_align_center_x(True)
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        log.debug("Checking position...")
        assert round(plot.get_position()[0],10) == round((90*12-plot.graphic.get_width())/2,10), "%s != %s" % (round(plot.get_position()[0],10),round((90*12-plot.graphic.get_width())/2,10))
        assert round(plot.get_position()[1],10) == 0, "%s != %s" % (round(plot.get_position()[1],10),0)

    def test_align_center_y(self):
        """ Makes sure the graphic is centered correctly in the y direction"""
        plot = Plot(90*12,90*12*4)
        plot.set_rotation(90)
        plot.set_padding(35,0,35,0)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        plot.set_align_center_y(True)
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        log.debug("Checking position...")
        assert round(plot.get_position()[0],10) == 0, "%s != %s" % (round(plot.get_position()[0],10),0)
        assert round(plot.get_position()[1],10) == round((90*12-70-plot.graphic.get_height())/2,10), "%s != %s" % (round(plot.get_position()[1],10),round((90*12-70-plot.graphic.get_height())/2,10))

    def test_align_center_y_2(self):
        """ Makes sure the graphic is centered correctly in the y direction"""
        plot = Plot(90*12,90*12*4)
        plot.set_rotation(90)
        plot.set_padding(35,0,35,0)
        plot.set_copies(7)
        plot.set_graphic(etree.tostring(etree.parse("arrow.svg")))
        h = plot.graphic.get_height()*5 + 4*plot.get_spacing()[1]
        plot.set_align_center_y(True)
        f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(plot.get_preview_xml())
        f.close()
        log.debug("Checking position...")
        assert round(plot.get_position()[0],10) == 0, "%s != %s" % (round(plot.get_position()[0],10),0)
        assert round(plot.get_position()[1],10) == round((90*12-70-h)/2,10), "%s != %s" % (round(plot.get_position()[1],10),round((90*12-70-h)/2,10))



