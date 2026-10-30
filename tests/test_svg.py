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


@pytest.mark.parametrize('path', glob('tests/data/*.svg'))
def test_svg(path):
    """ Make sure the document can be parsed """
    try:
        doc = QtSvgDoc(path)
    except NotImplementedError as e:
         pytest.skip(str(e))


@pytest.mark.parametrize('ids, paths', [
    (['g860'], ['path979']),
    (['g865'], ['path979', 'path981']),
])
def test_svg_select_group(ids, paths):
    """ Selecting a group by id must keep the paths inside it and nothing
    else (eg 'Cut selection' from Inkscape on text converted to paths)
    """
    path = 'tests/data/groups.svg'
    selected = QtSvgDoc(path, ids=ids)
    expected = QtSvgDoc(path, ids=paths)
    assert not selected.isEmpty()
    assert selected.elementCount() == expected.elementCount()
    assert selected.boundingRect() == expected.boundingRect()
