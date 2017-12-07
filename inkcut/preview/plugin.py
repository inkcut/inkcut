"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import pyqtgraph as pg
from atom.api import List, Instance, Enum
from enaml.qt import QtCore, QtGui
from inkcut.core.api import Plugin, Model, svg


class PlotBase(Model):
    #job = Instance(Job)
    plot = List()
    pen_media = Instance(QtGui.QPen)
    pen_media_padding = Instance(QtGui.QPen)
    pen_up = Instance(QtGui.QPen)
    pen_offset = Instance(QtGui.QPen)
    pen_down = Instance(QtGui.QPen)

    units = Enum(*svg.QtSvgDoc._uuconv.keys())

    def _default_units(self):
        return 'in'

    def _default_pen_media(self):
        return pg.mkPen((128, 128, 128))

    def _default_pen_media_padding(self):
        return pg.mkPen((128, 128, 128), style=QtCore.Qt.DashLine)

    def _default_pen_up(self):
        return pg.mkPen(hsv=(0.53, 1, 0.5, 0.5))

    def _default_pen_offset(self):
        return pg.mkPen(hsv=(0.43, 1, 0.5, 0.5))

    def _default_pen_down(self):
        return pg.mkPen((128, 128, 128))


class PreviewPlugin(Plugin):

    plot = Instance(PlotBase, ())

    def start(self):
        pass

