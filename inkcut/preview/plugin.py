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
from inkcut.core.api import Plugin, Model, unit_conversions
from inkcut.job.models import Job
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

    units = Enum(*unit_conversions.keys())

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

    #: Set's the plot that is drawn in the preview
    plot = Instance(PlotBase, ())

    #: The job currently being previewed
    job = Instance(Job)

    #: Fields that are observed
    observed = List(default=['model', 'material', 'material.padding',
                                  'material.size'])

    def start(self):
        """ Observe the job plugin to see when the job changs and update
        the preview accordingly.
        
        """
        plugin = self.workbench.get_plugin("inkcut.job")
        plugin.observe('job', self._observe_job)

    def stop(self):
        """ 
        
        """
        plugin = self.workbench.get_plugin("inkcut.job")
        plugin.unobserve('job', self._observe_job)

    def _default_job(self):
        plugin = self.workbench.get_plugin("inkcut.job")
        return plugin.job

    def _observe_job(self, change):
        """ Whenever the referenced job changes, update our observers
        so the preview update handlers are properly called
        """
        #: If this was an update from the other plugin, set the local
        #: reference which will fire this observer again
        job = change['value']
        if job != self.job:
            self.job = job
            return

        #: Unobserve any old handlers
        if change['type'] == 'update':
            old = change['oldvalue']
            for name in self.observed:
                old.unobserve(name, self._refresh_preview)

        #: Update new handlers
        for name in self.observed:
            job.observe(name, self._refresh_preview)

    def _refresh_preview(self, change):
        """ Redraw the preview on the screen 
        
        """
        view_items = []

        #: Transform used by the view
        t = QtGui.QTransform.fromScale(1, -1)

        job = self.job
        plot = self.plot

        if job.model:
            view_items.extend([
                PainterPathPlotItem(job.move_path, pen=plot.pen_up),
                PainterPathPlotItem(job.cut_path, pen=plot.pen_down)
            ])
            #: TODO: This
            #if self.show_offset_path:
            #    view_items.append(PainterPathPlotItem(
            # self.job.offset_path,pen=self.pen_offset))
        if job.material:
            # Also observe any change to job.media and job.device
            view_items.extend([
                PainterPathPlotItem(
                    job.material.path*t, pen=plot.pen_media,
                    skip_autorange=(False, [0, job.size[1]])),
                PainterPathPlotItem(
                    job.material.padding_path*t, pen=plot.pen_media_padding,
                    skip_autorange=True)
            ])

        #: Update the plot
        self.plot.plot = view_items
