"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
from atom.api import List, Instance, Enum, Bool, Range
from enaml.qt import QtCore, QtGui
from enaml.qt.QtGui import QPainterPath, QTransform
from enamlx.widgets.api import Pen

from inkcut.core.api import Plugin, Model, unit_conversions, log


class PreviewModel(Model):
    #: List of plot items to display
    items = List(dict)

    #: Internal paths for drawing
    paths = List(QPainterPath)

    #: Colors
    pen_media = Instance(Pen)
    pen_media_padding = Instance(Pen)
    pen_up = Instance(Pen)
    pen_offset = Instance(Pen)
    pen_down = Instance(Pen)
    pen_device = Instance(Pen)

    def _default_pen_media(self):
        return Pen(color="rgb(128, 128, 128)")

    def _default_pen_media_padding(self):
        return Pen(color="rgb(128, 128, 128)", line_style="dash")

    def _default_pen_device(self):
        return Pen(color="rgb(235, 194, 194)", line_style="dash")

    def _default_pen_up(self):
        return Pen(color="#00d0ff")

    def _default_pen_offset(self):
        return Pen(color="#ff00b2")

    def _default_pen_down(self):
        return Pen(color="rgb(128, 128, 128)")

    def init(self, view_items):
        self.paths = [QPainterPath(), QPainterPath()]
        default_items = [
            {'path': self.paths[0], 'pen': self.pen_down},
            {'path': self.paths[1], 'pen': self.pen_up},
        ]
        self.items = default_items+view_items

    def update(self, position):
        """ Watch the position of the device as it changes. """
        if not self.paths:
            return
        x, y, z = position
        if z:
            self.paths[0].lineTo(x, -y)
            self.paths[1].moveTo(x, -y)
            self.items[0].updateData(self.paths[0])
        else:
            self.paths[0].moveTo(x, -y)
            self.paths[1].lineTo(x, -y)
            self.items[1].updateData(self.paths[1])


class PreviewPlugin(Plugin):

    #: Set's the plot that is drawn in the preview
    preview = Instance(PreviewModel, ())

    #: Plot for showing live status
    live_preview = Instance(PreviewModel, ())

    #: Transform applied to all view items
    transform = Instance(QTransform)

    show_grid_x = Bool().tag(config=True)
    show_grid_y = Bool().tag(config=True)
    grid_alpha = Range(value=30, low=1, high=100).tag(config=True)


    def _default_transform(self):
        """ Qt displays top to bottom so this can be used to flip it.

        """
        return QTransform.fromScale(1, -1)

    def set_preview(self, *items):
        """ Sets the items that will be displayed in the plot

        Parameters
        ----------
        items: list of kwargs
            A list of kwargs to to pass to each plot item

        """
        self.preview.items = [i for i in items]

    def set_live_preview(self, *items):
        """ Set the items that will be displayed in the live plot preview.
        After set, use live_preview.update(position) to update it.

        Parameters
        ----------
        items: list of kwargs
            A list of kwargs to to pass to each plot item


        """
        self.live_preview.init([i for i in items])

