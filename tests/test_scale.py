"""
Copyright (c) 2018, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Mar 14, 2018

@author: jrm
"""
import os
import pytest
from glob import glob
from inkcut.core.utils import split_painter_path
from inkcut.core.svg import QtSvgDoc

def mm_to_inkcut_units(dim):
    # Scale the input (in mm) to Inkcut units
    return dim*90.0/25.4

# This is just about the limit of precision we can expect
# for ordinary scale items that would fit on a printer.
# We may have some rounding error below this precision.
def close_to(dim, otherdim):
    return abs(dim-otherdim) < 0.00001

def check_expected_dimensions(doc, x, y, width, height):
    subpaths = split_painter_path(doc)
    assert len(subpaths) == 1

    example_rectangle = subpaths[0]
    example_bounding_rect = example_rectangle.boundingRect()
    position = example_bounding_rect.topLeft()
    print(example_bounding_rect)
    print(position)

    assert close_to(position.x(), mm_to_inkcut_units(x))
    assert close_to(position.y(), mm_to_inkcut_units(y))
    assert close_to(example_bounding_rect.width(), mm_to_inkcut_units(width))
    assert close_to(example_bounding_rect.height(), mm_to_inkcut_units(height))


# There are many different ways to express the same
# SVG drawing with different units.  Here, we test that
# the same rectangle is expressed in different units, but
# we still exptect the imported result in terms of
# INKCUT_DPI units to be preserved.  That is, no matter how
# you express the units in the SVG document, we can always
# scale them so that they match 'actual real-world' cutting
# units.

# In order to do this, we create a rectangle at position 30mm,50mm
# with size 20mm wide and 10mm high.  We will express this
# with different units in different documents, but the invariant
# here is that the imported object in terms of Inkcut units
# should be the same for all of these documents.
@pytest.mark.parametrize('path', glob('tests/data/scale/*.svg'))
def test_scale(path):
    """ Make sure that we get the same result even if the unit of measure is different in the source documents settings """
    try:
        print("Loading document")
        print(path)
        doc = QtSvgDoc(path)
        print("Testing scale")

        check_expected_dimensions(doc, 30, 50, 20, 10)

    except NotImplementedError as e:
         pytest.skip(str(e))

def test_explicit_dpi_setting_90():
    """ Test that if we disable detection of inkscape DPI settings, we can still import at the correct scale with the explicit DPI setting """
    # We want to check that we can manually specify the DPI for
    # a document without relying on detecting the Inkscape version.
    doc = QtSvgDoc(
        "tests/data/scale/ScaleTest-px-with-viewbox-old-inkscape.svg",
        dpi_default = 90.0,
        dpi_auto_detect_inkscape = False)
    print("Just another test")
    check_expected_dimensions(doc, 30, 50, 20, 10)

def test_explicit_dpi_setting_96():
    """ Test that if we import with a different DPI setting, it will change the dimensions accordingly """
    # We want to check that we can manually specify the DPI for
    # a document without relying on detecting the Inkscape version.
    doc = QtSvgDoc(
        "tests/data/scale/ScaleTest-px-with-viewbox-old-inkscape.svg",
        dpi_default = 96.0,
        dpi_auto_detect_inkscape = False)
    print("Just another test")
    check_expected_dimensions(doc, 30*90/96, 50*90/96, 20*90/96, 10*90/96)
