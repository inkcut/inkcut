#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: test_graphic.py
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
"""Test suite to test the graphic.py file"""
import sys
import os
import logging

dirname = os.path.dirname
THIS_DIR = os.path.join(os.path.abspath(dirname(dirname(__file__))))
TEST_FILE_DIR = os.path.join(THIS_DIR,"tests","input_files")
sys.path.append(THIS_DIR)

from lxml import etree
from inkcut_lib.graphic import Graphic

log = logging.getLogger(__name__)
class TestPlot:
    def setUp(self):
        """Setup the Inkcut database and other application settings"""
        pass

    def tearDown(self):
        pass

    def test_graphic_from_string(self):
        """Create a graphic from string"""
        graphic = Graphic(etree.tostring(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg"))))
        f = open("tests/out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()

    def test_case_2(self):
        """Create a graphic from etree elements"""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        f = open("tests/out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()

    def test_case_3(self):
        """Check the graphic height"""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        e = 1
        h = 170.563
        assert h-e < graphic.get_height() < h+e, "Graphic height is wrong!"

    def test_case_4(self):
        """Check the graphic width"""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        e = 1
        w = 333.469
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong!"

    def test_case_5(self):
        """Check that graphic is scaled properly in the y direction."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_scale(2)
        e = 1
        h = 170.563*2
        assert h-e < graphic.get_height() < h+e, "Graphic height is wrong after scaling!"
        graphic.set_scale(1)
        h = 170.563
        assert h-e < graphic.get_height() < h+e, "Graphic height is wrong after scaling the second time!"

    def test_case_6(self):
        """Check that graphic is scaled properly in the x direction."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_scale(2)
        e = 1
        w = 333.469*2
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong after scaling!"
        graphic.set_scale(1)
        w = 333.469
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong after scaling the second time!"

    def test_scale_3(self):
        """Check that graphic is scaled properly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_scale(2.72)
        e = 1
        w = 333.469*2.72
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong after scaling!"
        graphic.set_scale(1)
        w = 333.469
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong after scaling the second time!"

    def test_scale_y(self):
        """Check that graphic is scaled properly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_scale(1,2)
        e = 1
        w = 333.469
        h = 170.563*2
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong after scaling!"
        assert h-e < graphic.get_height() < h+e, "Graphic height is wrong after scaling!"

    def test_scale_y(self):
        """Check that graphic is scaled properly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_scale(3,1)
        e = 1
        w = 333.469*3
        h = 170.563
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong after scaling!"
        assert h-e < graphic.get_height() < h+e, "Graphic height is wrong after scaling!"

    def test_mirror_x(self):
        """Check that graphic is mirrored properly about the x axis."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_mirror_x(True)
        f = open("tests/out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()

    def test_mirror_y(self):
        """Check that graphic is mirrored properly about the y axis."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_mirror_y(True)
        f = open("tests/out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()

    def test_double_mirror_x(self):
        """Check that graphic is mirrored x properly twice."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic2 = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_mirror_x(True)
        graphic.set_mirror_x(False)
        assert graphic.get_bounding_box() == graphic2.get_bounding_box(), "They should be the same!"

    def test_symmetric_x(self):
        """Check that a symmetric graphic is mirrored x properly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"rectangle.svg")).getroot())
        graphic2 = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"rectangle.svg")).getroot())
        graphic.set_mirror_x(True)
        assert graphic.get_bounding_box() == graphic2.get_bounding_box(), "They should be the same!"


    def test_double_mirror_y(self):
        """Check that graphic is mirrored y properly twice."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic2 = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_mirror_y(True)
        graphic.set_mirror_y(False)
        assert graphic.get_bounding_box() == graphic2.get_bounding_box(), "They should be the same!"

    def test_translate_1(self):
        """Check that graphic is translated properly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_position(0,0)
        log.info(graphic.get_position())
        assert map(lambda x: round(x,10),graphic.get_position()) == [0,0], "Position should be 0,0!"

    def test_translate_2(self):
        """Check that graphic is translated properly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_position(500,237.21)
        f = open("tests/out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()
        assert map(lambda x: round(x,10),graphic.get_position()) == [500,237.21], "Position should be 500,237.21!"

    def test_translate_3(self):
        """Check that graphic is translated properly twice."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.set_position(500,237.21)
        graphic.set_position(11,32)
        assert map(lambda x: round(x,10),graphic.get_position()) == [11,32], "Position should be 11,32!"

    def test_rotation_1(self):
        """Check that graphic is rotated properly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        h = graphic.get_height()
        graphic.set_rotation(90)
        assert graphic.get_width() == h

    def test_rotation_2(self):
        """Check that graphic is rotated properly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        h = graphic.get_height()
        graphic.set_rotation(270)
        f = open("tests/out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()
        assert graphic.get_width() == h

    def test_rotation_3(self):
        """Check that graphic is rotated properly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        pos = graphic.get_position()
        graphic.set_rotation(23.21)
        f = open("tests/out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()
        assert graphic.get_position() == pos

    def test_rotation_4(self):
        """Check that graphic is rotated properly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        xml = graphic.get_xml()
        graphic.set_rotation(23.21)
        graphic.set_rotation(0)
        assert  graphic.get_xml() == xml

    def test_weedline(self):
        """Check a weedline is added correctly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        pos = graphic.get_position()
        graphic.set_weedline(True)
        f = open("tests/out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()
        assert  graphic.get_position() == pos

    def test_weedline_2(self):
        """Check a weedline is removed correctly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        data = graphic._get_debug_data()
        graphic.set_weedline(True)
        graphic.set_weedline(False)
        assert  graphic._get_debug_data() == data

    def test_weedline_3(self):
        """Check a weedline padding is added correctly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        h = graphic.get_height()
        w = graphic.get_width()
        graphic.set_weedline_padding(100)
        graphic.set_weedline(True)
        f = open("tests/out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()
        assert  graphic.get_height() == h+200
        assert  graphic.get_width() == w+200

    def test_weedline_4(self):
        """Check a weedline padding is added correctly in reverse order."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        h = graphic.get_height()
        w = graphic.get_width()
        pos = graphic.get_position()
        graphic.set_weedline(True)
        graphic.set_weedline_padding(10)
        assert  graphic.get_height() == h+20
        assert  graphic.get_width() == w+20
        assert  graphic.get_position() == pos

    def test_weedline_5(self):
        """Check a weedline padding is removed correctly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        h = graphic.get_height()
        w = graphic.get_width()
        pos = graphic.get_position()
        graphic.set_weedline_padding(10)
        graphic.set_weedline(True)
        graphic.set_weedline_padding(0)
        assert  graphic.get_height() == h
        assert  graphic.get_width() == w
        assert  graphic.get_position() == pos

    def test_adjusted_bbox(self):
        """Check that get_bounding_box(adjusted=True) works correctly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        bbox = graphic.get_bounding_box()
        h = graphic.get_height()
        w = graphic.get_width()
        graphic.set_weedline_padding(10)
        graphic.set_weedline(True)
        assert  graphic.get_width(adjusted=True) == w, "%s != %s" %(graphic.get_width(adjusted=True),w)
        assert  graphic.get_height(adjusted=True) == h, "%s != %s" %(graphic.get_height(adjusted=True),h)
        log.debug(bbox)
        log.debug(graphic.get_bounding_box(adjusted=True))
        assert  graphic.get_bounding_box(adjusted=True) == bbox

    def test_changed_flag(self):
        """Check that changed flag works correctly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"arrow.svg")).getroot())
        graphic.reset_changed_flag()
        graphic.set_mirror_x(True)
        assert graphic.get_changed_flag(), "Changed flag should be set!"
        graphic.reset_changed_flag()
        graphic.set_mirror_x(False)
        assert graphic.get_changed_flag(), "Changed flag should be set!"
        graphic.reset_changed_flag()
        graphic.set_scale(2)
        assert graphic.get_changed_flag(), "Changed flag should be set!"
        graphic.reset_changed_flag()
        graphic.set_rotation(2)
        assert graphic.get_changed_flag(), "Changed flag should be set!"
        graphic.reset_changed_flag()
        graphic.set_position(2,500)
        assert not graphic.get_changed_flag(), "Changed flag should not be set!"
        graphic.reset_changed_flag()
        graphic.set_weedline(True)
        assert graphic.get_changed_flag(), "Changed flag should be set!"

    def test_get_polyline(self):
        """ Check that get polyline works correctly."""
        graphic = Graphic(etree.parse(os.path.join(TEST_FILE_DIR,"fat-giraffes.svg")))
        f = open("pout.py","w")
        f.write("poly = %s"%graphic.get_polyline())
        f.close()
