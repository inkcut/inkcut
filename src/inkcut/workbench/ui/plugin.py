# -*- coding: utf-8 -*-
'''
Created on Jul 14, 2015

@author: jrm
'''
import os
import traceback
from atom.api import Instance,Bool,Int,Unicode,ContainerList,Enum, observe
from enaml.qt import QtGui,QtCore
from enaml.application import timed_call
from enaml.widgets.page import Page
from inkcut.workbench.core.utils import SingletonPlugin, ConfigurableAtom
from inkcut.workbench.ui.widgets.plot_view import PainterPathPlotItem
from inkcut.workbench.core.job import Job
from inkcut.workbench.core.svg import QtSvgDoc
import pyqtgraph as pg


class PlotBase(ConfigurableAtom):
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
        return pg.mkPen((128,128,128))
    
    def _default_pen_media_padding(self):
        return pg.mkPen((128,128,128),style=QtCore.Qt.DashLine)
    
    def _default_pen_up(self):
        return pg.mkPen(hsv=(0.53,1,0.5,0.5))
    
    def _default_pen_offset(self):
        return pg.mkPen(hsv=(0.43,1,0.5,0.5))
    
    def _default_pen_down(self):
        return pg.mkPen((128,128,128))#,hsv=(0.53,1,0.5,0.5))
    


class LivePlot(PlotBase):
    progress = Int(0)
    running = Bool(False)
    paused = Bool(False)
    cancelled = Bool(False)
    
    paths = ContainerList(Instance(QtGui.QPainterPath))
    
    def start_plot(self):
        """ Runs the do_plot command in a non-blocking way
        
        """
        if self.running:
            self.log.debug("Already plotting!...")
            return
        
        self.log.debug("Starting job...")
        
        # Clear plot
        self._view_changed(None)
        # Draw the media 
        
        tasks = self.do_plot()
        self.paused = False
        self.cancelled = False
        
        def task():
            self.running = True
            try:
                timeout = tasks.next()
                if timeout is not None:
                    timed_call(timeout, task)
            except (StopIteration):
                self.running = False
        
        timed_call(0, task)
        
        
    def do_plot(self):
        """ Actually do the plot and send commands to the device
        1. Init the device
        2. For each point in the interpolated path:
            1. Send point to the device
            2. Wait desired time (yield the timeout)
        3. Close the device
        
        """
        # TODO: Push into a plugin
        yield 1
        self.job.device.init()
        #speed = self.device.speed # Units/second
        # device.speed is in CM/s
        # d is in PX so...
        # speed = distance/seconds  
        # So distance/speed = seconds to wait
        try:
            step_size = 1
            step_time = max(1,round(1000*step_size/QtSvgDoc.parseUnit('%scm'%self.job.device.speed)))
            p_len = self.job.model.length()
            p_moved = 0
            _p = QtCore.QPointF(0,0) # previous point
            dl = step_size
            self.progress = 0
            x,y,z = (0,0,0) # head state
            
            for path in self.job.model.toSubpathPolygons():
                for i,p in enumerate(path):
                    subpath = QtGui.QPainterPath()
                    subpath.moveTo(_p)
                    subpath.lineTo(p)
                    l = subpath.length()
                    z = i!=0 and 1 or 0
                    d = 0
                    
                    # Interpolate path in steps of dl and ensure we get _p and p (t=0 and t=1)
                    while d<=l:# and self.isVisible():
                        if self.cancelled:
                            return
                        if self.paused:
                            yield 100 # ms
                            continue # Keep waiting...
                            
                        sp = subpath.pointAtPercent(subpath.percentAtLength(d))
                        if d==l:
                            break
                        
                        p_moved+=min(l-d,dl)
                        d = min(l,d+dl)
                    
                        x,y = sp.x(),-sp.y()
                        self.job.device.move(x,y,z)
                        self.progress = int(round(100*p_moved/p_len))
                        yield step_time # ms
                    
                    _p = p
        except:
            self.log.error(traceback.format_exc())
                
        finally:
            self.job.device.close()
            
    def _observe_running(self,change):
        if self.running:
            self.job.device.observe('position',self._position_changed)
        else:
            self.job.device.unobserve('position',self._position_changed)
            
    @observe('job','job.media','job.device')
    def _view_changed(self,change):
        view_items = []
        t=QtGui.QTransform.fromScale(1,-1)
        
        self.paths = [QtGui.QPainterPath(),QtGui.QPainterPath()]
        
        view_items.append(PainterPathPlotItem(self.paths[0],pen=self.pen_down))
        view_items.append(PainterPathPlotItem(self.paths[1],pen=self.pen_up))
        
        
        if self.job.media:
            # Also observe any change to job.media and job.device
            view_items.append(PainterPathPlotItem(self.job.media.path*t,pen=self.pen_media,skip_autorange=True))
            view_items.append(PainterPathPlotItem(self.job.media.padding_path*t,pen=self.pen_media_padding,skip_autorange=True))
        self.plot = view_items
        return view_items
    
    def _position_changed(self,change):
        x,y,z = change['value']
        if z:
            self.paths[0].lineTo(x,-y)
            self.paths[1].moveTo(x,-y)
            self.plot[0].updateData(self.paths[0])
        else:
            self.paths[0].moveTo(x,-y)
            self.paths[1].lineTo(x,-y)
            self.plot[1].updateData(self.paths[1])
            
        
    
            

class MainViewPlugin(SingletonPlugin,PlotBase):
    status = Unicode('None')
    
    current_document = Unicode('/home/jrm/Pictures/rome.svg')
    recent_documents = ContainerList(Unicode())
    show_offset_path = Bool()
    
    pages = ContainerList(Instance(Page))
    
    def start(self):
        self.workbench.register_plugins('inkcut/plugins')
    
    def _default_job(self):
        return Job(document=self.current_document)
    
    @observe('job','job.model','job.media','job.device')
    def _view_changed(self,change):
        view_items = []
        t=QtGui.QTransform.fromScale(1,-1)
        if self.job.model:
            view_items.append(PainterPathPlotItem(self.job.move_path,pen=self.pen_up))
            view_items.append(PainterPathPlotItem(self.job.cut_path,pen=self.pen_down))
            if self.show_offset_path:
                view_items.append(PainterPathPlotItem(self.job.offset_path,pen=self.pen_offset))
        if self.job.media:
            # Also observe any change to job.media and job.device
            view_items.append(PainterPathPlotItem(self.job.media.path*t,pen=self.pen_media,skip_autorange=(False,[0,self.job.size[1]])))
            view_items.append(PainterPathPlotItem(self.job.media.padding_path*t,pen=self.pen_media_padding,skip_autorange=True))
            
        self.plot = view_items
        
    
    @property
    def window(self):
        ui = self.workbench.get_plugin('enaml.workbench.ui')
        return ui.window.proxy.widget
    
    def close_document(self):
        pass
    
    def open_document(self, path=""):
        """ Sets the current file path, which fires _current_document_changed """
        if path=="" or not os.path.exists(path):
            open_dir = self.current_document
            if not os.path.exists(self.current_document) and self.recent_documents:
                for document in self.recent_documents:
                    open_dir = document
                    break
            
            path = QtGui.QFileDialog.getOpenFileName(self.window, self.window.tr("Open SVG File"),open_dir, "*.svg")[0]
        
        if not os.path.exists(path):
            self.log.debug("Cannot open %s, it does not exist!"%path)
            return
        
        # Close any old docs
        self.close_document()
        
        # Instead of append so we get a changed event
        self.recent_documents.append(path)
        self.current_document = path
        # Plot actually opened in _current_document_changed
        
    def start_job(self,job=None):
        # TODO: Copy other params as well
        job = job or self.job
        if not job.document:
            return
        model = LivePlot(job=job,units=self.units)
        import enaml
        with enaml.imports():
            from inkcut.workbench.ui.task_dialog import JobTaskDialog
        
        ui = self.workbench.get_plugin('enaml.workbench.ui')
        task = JobTaskDialog(ui.window,model=model).exec_()
        
    def _observe_current_document(self,change):
        self.job = Job(document=self.current_document)
        
