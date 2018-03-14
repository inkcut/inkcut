"""
Copyright (c) 2018, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Mar 14, 2018

@author: jrm
"""
import os
import pytest

from inkcut.core.svg import QtSvgDoc


@pytest.mark.parametrize('path', [
    'arc.svg'
])
def test_svg(path):
    f = os.path.join('tests', 'data', path)
    doc = QtSvgDoc(f)
