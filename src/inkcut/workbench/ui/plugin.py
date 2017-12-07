# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 14, 2015

@author: jrm
"""
import os
import traceback

import pyqtgraph as pg

from atom.api import (Instance, ForwardInstance, Bool, Int, Unicode,
                      ContainerList, Enum, observe)
from enaml.qt import QtGui,QtCore
from enaml.application import timed_call
from enaml.widgets.page import Page
from inkcut.workbench.core.utils import SingletonPlugin
from inkcut.workbench.preferences.plugin import Model
from inkcut.workbench.ui.widgets.plot_view import PainterPathPlotItem
from inkcut.workbench.core.job import Job
from inkcut.workbench.core.svg import QtSvgDoc
from inkcut.workbench.core.media import Media
from inkcut.workbench.core.device import Device


class PlotBase(Model):
    job = Instance(Job)
    plot = ContainerList()
    pen_media = Instance(QtGui.QPen)
    pen_media_padding = Instance(QtGui.QPen)
    pen_up = Instance(QtGui.QPen)
    pen_offset = Instance(QtGui.QPen)
    pen_down = Instance(QtGui.QPen)
    
    units = Enum(*QtSvgDoc._uuconv.keys())
    
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
        return pg.mkPen((128, 128, 128)) #,hsv=(0.53,1,0.5,0.5))
    

class LivePlot(PlotBase):
    #: Device to watch
    device = Instance(Device)
    
    #: Job to send to the device
    job = Instance(Job)
    
    #: Internal paths for drawing
    paths = ContainerList(Instance(QtGui.QPainterPath))
    
    def start_plot(self):
        """ Runs the do_plot command in a non-blocking way
        
        """
        if self.device.busy:
            self.log.error("Device is busy!...")
            return
        
        # Clear plot
        self._view_changed(None)
        
        self.log.debug("Starting job on device {} ...".format(
            self.device.name))

        #: Send the job to the device
        self.device.submit(self.job)
    
    @observe('job', 'job.media', 'device')
    def _view_changed(self, change):
        view_items = []
        t=QtGui.QTransform.fromScale(1, -1)
        
        self.paths = [QtGui.QPainterPath(), QtGui.QPainterPath()]
        
        view_items.append(PainterPathPlotItem(self.paths[0],
                                              pen=self.pen_down))
        view_items.append(PainterPathPlotItem(self.paths[1],
                                              pen=self.pen_up))

        if self.job and self.job.media:
            # Also observe any change to job.media and job.device
            view_items.append(PainterPathPlotItem(
                self.job.media.path*t, pen=self.pen_media,
                skip_autorange=True))
            view_items.append(PainterPathPlotItem(
                self.job.media.padding_path*t, pen=self.pen_media_padding,
                skip_autorange=True))
        self.plot = view_items
    
    @observe('device.position')
    def _position_changed(self,change):
        """ Watch the position of the device as it changes. """
        x, y, z = change['value']
        if z:
            self.paths[0].lineTo(x, -y)
            self.paths[1].moveTo(x, -y)
            self.plot[0].updateData(self.paths[0])
        else:
            self.paths[0].moveTo(x, -y)
            self.paths[1].lineTo(x, -y)
            self.plot[1].updateData(self.paths[1])
            
        
class MainViewPlugin(SingletonPlugin, PlotBase):
    status = Unicode('None')
    
    #: Wiki page
    wiki_page = Unicode('http://www.google.com')
    
    #: Current opened document
    current_document = Unicode().tag(config=True)
    
    #: Previously opened documents
    recent_documents = ContainerList(Unicode()).tag(config=True)
    
    #: Show the path after running through the device
    show_offset_path = Bool().tag(config=True)
    
    #: Media library list
    available_media = ContainerList(Instance(Media)).tag(config=True)
    
    #: Configured devices
    available_devices = ContainerList(Instance(Device)).tag(config=True)
    
    #: Currently selected device
    device = Instance(Device).tag(config=True)
    
    #: Currently selected media
    media = Instance(Media).tag(config=True)
    
    #: UI tabs
    pages = ContainerList(Instance(Page))
    
    def start(self):
        self.log.info("Device {}".format(self.device))
        pass
#         if not self.available_devices:
#             self.available_devices = [self.create_new_device()]
#         if not self.available_media:
#             self.available_media = [self.create_new_media()]
#         print self.available_devices
        # Link core device and media to the job
        #core = self.workbench.get_plugin('inkcut.workbench.core')
        #self.observe('device',lambda change:setattr(self.job,'device',change['value']))
        #core.observe('media',lambda change:setattr(self.job,'media',change['value']))
    
    def _default_device(self):
        try:
            from inkcut.plugins.jeffy.jeffy import JeffyDevice
            d = JeffyDevice()
        except ImportError:
            d = Device(name="Test")
            from inkcut.plugins.protocols.hpgl import HPGLProtocol
            d.protocol = HPGLProtocol()
            d.transport = "serial"
        return d
        #if not self.available_devices:
        #    self.available_devices = [self.create_new_device()]
        #return self.available_devices[0]
    
    def _default_media(self):
        if not self.available_media:
            self.available_media = [self.create_new_media()]
        return self.available_media[0]
    
    def _default_job(self):
        #core = self.workbench.get_plugin('inkcut.workbench.core')
        try:
            return Job(document=self.current_document,
                       media=self.media)
        except Exception as e:
            context = dict(doc=self.current_document,msg=e)
            self.log.error(traceback.format_exc())
            self.workbench.show_critical(
                "Error opening {doc}".format(**context),
                "Sorry, could not open {doc}.\n\n"
                "Error: {msg}".format(**context))
            return Job(media=self.media)
    
    @observe('job', 'job.model',
             'media', 'media.padding', 'media.size')
    def _view_changed(self, change):
        """ Redraw the path on the screen """
        view_items = []
        t=QtGui.QTransform.fromScale(1, -1)
        if self.job.model:
            view_items.append(PainterPathPlotItem(self.job.move_path,
                                                  pen=self.pen_up))
            view_items.append(PainterPathPlotItem(self.job.cut_path,
                                                  pen=self.pen_down))
            #: TODO: This
            #if self.show_offset_path:
            #    view_items.append(PainterPathPlotItem(
            # self.job.offset_path,pen=self.pen_offset))
        if self.job.media:
            # Also observe any change to job.media and job.device
            view_items.append(PainterPathPlotItem(
                self.job.media.path*t, pen=self.pen_media,
                skip_autorange=(False, [0, self.job.size[1]])))
            view_items.append(PainterPathPlotItem(
                self.job.media.padding_path*t, pen=self.pen_media_padding,
                skip_autorange=True))
        self.plot = view_items
        #self.workbench.save_config()
        
    @observe('media', 'job.media')
    def _media_changed(self, change):
        """ Bind UI media to job media """ 
        self.job.media = self.media
    
    @property
    def window(self):
        ui = self.workbench.get_plugin('enaml.workbench.ui')
        return ui.window.proxy.widget
    
    def close_document(self):
        """ Set the current document to nothing
            and start a new empty job
        """ 
        self.current_document = ''
        if self.job:
            self.job = Job(media=self.media)
    
    def open_document(self, path=""):
        """ Sets the current file path, 
            which fires _current_document_changed 
        """
        if path == "" or not os.path.exists(path):
            open_dir = self.current_document
            if not os.path.exists(self.current_document) \
                    and self.recent_documents:
                for document in self.recent_documents:
                    open_dir = document
                    break
            
            path = QtGui.QFileDialog.getOpenFileName(
                self.window, self.window.tr("Open SVG File"), open_dir,
                "*.svg")
            if not path:
                return # Cancelled
            self.log.debug(path)
            
        if isinstance(path, (list, tuple)):
            path = path[0]
        if not os.path.exists(path):
            self.log.debug("Cannot open %s, it does not exist!" % path)
            return
        
        if not os.path.isfile(path):
            self.log.debug("Cannot open %s, it is not a file!" % path)
            return
        
        # Close any old docs
        self.close_document()
        
        # Instead of append so we get a changed event
        if path not in self.recent_documents:
            self.recent_documents.append(path)
            
        self.log.info("Opening {doc}".format(doc=path))
        self.current_document = path
        # Plot actually opened in _current_document_changed
        
    def _observe_current_document(self, change):
        """ When the current document is updated, Create a new job with 
        the document.
        
        """
        if self.current_document:
            self.job = self._default_job()
            
#     def _observe_recent_documents(self,change):
#         """ Make sure the recent documents all exist
#             or remove them from the list.
#         """
#         self.recent_documents = [doc for doc in self.recent_documents 
#                                         if os.path.isfile(doc)]
    
    def create_new_media(self):
        return Media()
    
    def create_new_device(self):
        core = self.workbench.get_plugin('inkcut.workbench.core')
        return Device(
            name="New device",
            supported_protocols=core.available_protocols,
        )
    
    #def _observe_recent_documents(self,change):
    #    if change['type']!='create':
    #        ui = self.workbench.get_plugin('enaml.workbench.ui')
    #        ui._refresh_actions()
#         # Trigger a ui action refresh when this changes
#         return
#         try:
#             self.workbench.unregister('inkcut.workspace.ui.recent_docs')
#         except ValueError:
#             pass
#         try:
#             import enaml
#             with enaml.imports():
#                 from inkcut.workbench.ui.manifest import RecentDocsManifest
#             self.workbench.register(RecentDocsManifest())
#         except ValueError:
#             pass
