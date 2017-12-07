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
from inkcut.core.api import Plugin, Model, unit_conversions, log
from .plot_view import PainterPathPlotItem
QPen = QtGui.QPen


class PlotBase(Model):
    #: List of plot items to display
    plot = List()

    #: Colors
    pen_media = Instance(QPen)
    pen_media_padding = Instance(QPen)
    pen_up = Instance(QPen)
    pen_offset = Instance(QPen)
    pen_down = Instance(QPen)
    pen_device = Instance(QPen)

    units = Enum(*unit_conversions.keys())

    def _default_units(self):
        return 'in'

    def _default_pen_media(self):
        return pg.mkPen((128, 128, 128))

    def _default_pen_media_padding(self):
        return pg.mkPen((128, 128, 128), style=QtCore.Qt.DashLine)

    def _default_pen_device(self):
        return pg.mkPen((235, 194, 194), style=QtCore.Qt.DashLine)

    def _default_pen_up(self):
        return pg.mkPen(hsv=(0.53, 1, 0.5, 0.5))

    def _default_pen_offset(self):
        return pg.mkPen(hsv=(0.43, 1, 0.5, 0.5))

    def _default_pen_down(self):
        return pg.mkPen((128, 128, 128))


class PreviewPlugin(Plugin):

    #: Set's the plot that is drawn in the preview
    plot = Instance(PlotBase, ())

    #: Transform applied to all view items
    transform = Instance(QtGui.QTransform)

    def _default_transform(self):
        """ Qt displays top to bottom so this can be used to flip it. 
        
        """
        return QtGui.QTransform.fromScale(1, -1)

    def set_preview(self, *items):
        """ Sets the items that will be displayed in the plot
        
        Parameters
        ----------
        items: list of kwargs
            A list of kwargs to to pass to each plot item 

        """
        t = self.transform
        view_items = [
            PainterPathPlotItem(kwargs.pop('path'), **kwargs)
            for kwargs in items
        ]
        self.plot.plot = view_items