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

from .models import Job, Media


class JobPlugin(Plugin):
    #: Units
    units = Enum(*svg.QtSvgDoc._uuconv.keys())

    #: Current mdeida
    media = Instance(Media, ())

    #: Current job
    job = Instance(Job)

    def _default_job(self):
        return Job(media=self.media)

    def _default_units(self):
        return 'in'

    def start(self):
        pass

