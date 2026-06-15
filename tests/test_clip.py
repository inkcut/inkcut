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

from inkcut.core.svg import QtSvgDoc
from inkcut.job.filters import ClipFilter
from inkcut.job.models import Job

# This is just about the limit of precision we can expect
# for ordinary scale items that would fit on a printer.
# We may have some rounding error below this precision.
def close_to(dim, otherdim):
    return abs(dim-otherdim) < 0.00001

# Here, we check that our assertions for this test case are covered.
def expect_dimensions(path, x, y, width, height):
        clipped_bbox = path.boundingRect()
        # Check that if we don't clip, we end up with
        # a bounding rectangle that is the same before and
        # after the clip.
        assert close_to(x, clipped_bbox.x())
        assert close_to(y, clipped_bbox.y())
        assert close_to(width, clipped_bbox.width())
        assert close_to(height, clipped_bbox.height())

# Here, we apply the clip filter (or not)
# depending on which case we're testing.
def check_clip_filter(doc, clip):
        job = Job()
        job.clip_to_plot_area = clip

        # Set the material dimensions
        job.material.padding[0] = 0
        job.material.padding[1] = 0
        job.material.padding[2] = 0
        job.material.padding[3] = 0
        job.material.size[0] = 25
        job.material.size[1] = 25
        
        filters = ClipFilter.get_filter_options(job, doc)
        clipped_path = filters[0].apply_filter(job, doc)
        
        return clipped_path
        
def test_disable_clipping():
    """ Check that we can clip an SVG document to the correct size """
    try:
        path = "tests/data/clip/clip_test.svg"
        doc = QtSvgDoc(path)
        clipped_path = check_clip_filter(doc, False)
        original_bbox = doc.boundingRect()
        expect_dimensions(clipped_path, original_bbox.x(), original_bbox.y(), original_bbox.width(), original_bbox.height())

    except NotImplementedError as e:
         pytest.skip(str(e))

def test_enable_clipping():
    """ Check that we can clip an SVG document to the correct size """
    try:
        path = "tests/data/clip/clip_test.svg"
        doc = QtSvgDoc(path)
        clipped_path = check_clip_filter(doc, True)
        expect_dimensions(clipped_path, 0, 0, 25, 25)
    except NotImplementedError as e:
         pytest.skip(str(e))
         
