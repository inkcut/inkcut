"""
Copyright (c) 2022, Karlis Senko

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Nov 3, 2022

@author: karliss
"""
import pytest
from enaml.qt.QtGui import QVector2D

import inkcut.job.ordering as ordering
import inkcut.core.utils as utils
from inkcut.core.svg import QtSvgDoc
from inkcut.job.plugin import JobPlugin
from inkcut.core.api import to_unit

DATA_PREFIX = "tests/data/path_ordering/"

EXPECTED_RANGES_RECT = {
    'OrderNormal': (4137, 4138),
    'OrderReversed': (4137, 4138),
    'OrderMinX': (6000, 8000),
    'OrderMaxX': (6000, 8000),
    'OrderMinY': (6000, 8000),
    'OrderMaxY': (6000, 8000),
    'OrderShortestPath': (2683, 2684),
    'OrderHilbert': (2564, 2565),
    'OrderZCurve': (3716, 3718),
}


@pytest.mark.parametrize('order', ordering.REGISTRY.values())
def test_basic(order):
    """ Basic test that orders run without errors.

    """
    name = order.__name__
    path = DATA_PREFIX + "/rect.svg"
    job_plugin = JobPlugin()  # only for settings
    sorter = order(plugin=job_plugin)
    doc = QtSvgDoc(path)

    sorted_path = sorter.order(None, doc)
    assert sorted_path
    path_items = utils.split_painter_path(sorted_path)
    assert len(utils.split_painter_path(doc)) == len(path_items)

    move_length = ordering.OrderHandler.subpath_move_distance(QVector2D(0, 0), path_items)
    expected = EXPECTED_RANGES_RECT[name]
    assert expected[0] <= move_length <= expected[1]


EXPECTED_SHORTEST = [
    ["lines.svg", (180-0.5, 180+0.5)],
    ["grid.svg", (185, 186)],
    ["sequence.svg", (420, 600)]
]


@pytest.mark.parametrize('path,expected', EXPECTED_SHORTEST)
def test_shortest_path(path, expected):
    job_plugin = JobPlugin()  # only for settings
    sorter = ordering.OrderShortestPath(plugin=job_plugin)
    doc = QtSvgDoc(DATA_PREFIX + path)

    sorted_path = sorter.order(None, doc)
    path_items = utils.split_painter_path(sorted_path)
    assert len(utils.split_painter_path(doc)) == len(path_items)

    move_length = ordering.OrderHandler.subpath_move_distance(QVector2D(0, 0), path_items)
    move_length = to_unit(move_length, "mm")
    assert expected[0] <= move_length <= expected[1]
