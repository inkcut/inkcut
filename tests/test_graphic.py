#!/usr/bin/env python
"""Test suite to test the graphic.py file"""
import sys
import os
import logging

dirname = os.path.dirname
sys.path.append(os.path.join(os.path.abspath(dirname(dirname(__file__))),'app'))
import inkcut

from lxml import etree
from lib.graphic import Graphic

log = logging.getLogger(__name__)
class TestPlot:
    def setUp(self):
        """Setup the Inkcut database and other application settings"""
        pass

    def tearDown(self):
        pass

    def test_graphic_from_string(self):
        """Create a graphic from string"""
        graphic = Graphic(etree.tostring(etree.parse("arrow.svg")))
        f = open("out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()

    def test_case_2(self):
        """Create a graphic from etree elements"""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        f = open("out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()

    def test_case_3(self):
        """Check the graphic height"""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        e = 1
        h = 170.563
        assert h-e < graphic.get_height() < h+e, "Graphic height is wrong!"

    def test_case_4(self):
        """Check the graphic width"""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        e = 1
        w = 333.469
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong!"

    def test_case_5(self):
        """Check that graphic is scaled properly in the y direction."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        graphic.set_scale(2)
        e = 1
        h = 170.563*2
        assert h-e < graphic.get_height() < h+e, "Graphic height is wrong after scaling!"
        graphic.set_scale(1)
        h = 170.563
        assert h-e < graphic.get_height() < h+e, "Graphic height is wrong after scaling the second time!"

    def test_case_6(self):
        """Check that graphic is scaled properly in the x direction."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        graphic.set_scale(2)
        e = 1
        w = 333.469*2
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong after scaling!"
        graphic.set_scale(1)
        w = 333.469
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong after scaling the second time!"

    def test_scale_3(self):
        """Check that graphic is scaled properly."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        graphic.set_scale(2.72)
        e = 1
        w = 333.469*2.72
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong after scaling!"
        graphic.set_scale(1)
        w = 333.469
        assert w-e < graphic.get_width() < w+e, "Graphic width is wrong after scaling the second time!"

    def test_mirror_x(self):
        """Check that graphic is mirrored properly about the x axis."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        graphic.set_mirror_x(True)
        f = open("out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()

    def test_mirror_y(self):
        """Check that graphic is mirrored properly about the y axis."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        graphic.set_mirror_y(True)
        f = open("out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()

    def test_double_mirror_x(self):
        """Check that graphic is mirrored x properly twice."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        graphic2 = Graphic(etree.parse("arrow.svg").getroot())
        graphic.set_mirror_x(True)
        graphic.set_mirror_x(False)
        assert graphic.get_xml() == graphic2.get_xml(), "They should be the same!"

    def test_symmetric_x(self):
        """Check that a symmetric graphic is mirrored x properly."""
        graphic = Graphic(etree.parse("rectangle.svg").getroot())
        graphic2 = Graphic(etree.parse("rectangle.svg").getroot())
        graphic.set_mirror_x(True)
        assert graphic.get_bounding_box() == graphic2.get_bounding_box(), "They should be the same!"


    def test_double_mirror_y(self):
        """Check that graphic is mirrored y properly twice."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        graphic2 = Graphic(etree.parse("arrow.svg").getroot())
        graphic.set_mirror_y(True)
        graphic.set_mirror_y(False)
        assert graphic.get_xml() == graphic2.get_xml(), "They should be the same!"

    def test_translate_1(self):
        """Check that graphic is translated properly."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        graphic.set_position(0,0)
        log.info(graphic.get_position())
        assert map(lambda x: round(x,10),graphic.get_position()) == [0,0], "Position should be 0,0!"

    def test_translate_2(self):
        """Check that graphic is translated properly."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        graphic.set_position(500,237.21)
        f = open("out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()
        assert map(lambda x: round(x,10),graphic.get_position()) == [500,237.21], "Position should be 500,237.21!"

    def test_translate_3(self):
        """Check that graphic is translated properly twice."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        graphic.set_position(500,237.21)
        graphic.set_position(11,32)
        assert map(lambda x: round(x,10),graphic.get_position()) == [11,32], "Position should be 11,32!"

    def test_rotation_1(self):
        """Check that graphic is rotated properly."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        h = graphic.get_height()
        graphic.set_rotation(90)
        assert graphic.get_width() == h

    def test_rotation_2(self):
        """Check that graphic is rotated properly."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        h = graphic.get_height()
        graphic.set_rotation(270)
        f = open("out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()
        assert graphic.get_width() == h

    def test_rotation_3(self):
        """Check that graphic is rotated properly."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        pos = graphic.get_position()
        graphic.set_rotation(23.21)
        f = open("out/arrow_%s.svg"%sys._getframe().f_code.co_name,"w")
        f.write(graphic.get_xml())
        f.close()
        assert graphic.get_position() == pos

    def test_rotation_4(self):
        """Check that graphic is rotated properly."""
        graphic = Graphic(etree.parse("arrow.svg").getroot())
        xml = graphic.get_xml()
        graphic.set_rotation(23.21)
        graphic.set_rotation(0)
        assert  graphic.get_xml() == xml
