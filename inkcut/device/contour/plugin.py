# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 10, 2015

@author: jrm
"""
from atom.api import ContainerList, Float
from inkcut.core.api import Plugin


class ContourPlugin(Plugin):

    #: Start point
    start_point = ContainerList(Float(strict=False))

    #: End point
    end_point = ContainerList(Float(strict=False))