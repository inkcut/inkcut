# -*- coding: utf-8 -*-
'''
Created on Jul 19, 2015

@author: jrm
'''
from atom.api import Instance,Int,observe
from enaml.qt import QtGui, QtCore
from inkcut.workbench.core.utils import Plugin
from inkcut.workbench.core.device import Device
from inkcut.workbench.ui.plugin import PlotBase
from inkcut.workbench.ui.widgets.plot_view import PainterPathPlotItem

class JoystickPlugin(Plugin,PlotBase):
    
    device = Instance(Device)
    rate = Int(10)
    path = Instance(QtGui.QPainterPath)
    
    def start(self):
        pass
    
    def _observe_device(self,change):
        self.device.init()
            
    @observe('device')
    def _view_changed(self,change):
        view_items = []
        t=QtGui.QTransform.fromScale(1,-1)
        
        self.path = QtGui.QPainterPath()#[#],QtGui.QPainterPath()]
        x,y,z = self.device.position
        r= max(10,self.device.blade_offset)#,self.device.blade_offset
        self.path.addEllipse(QtCore.QPointF(x,-y),r,r)
        #view_items.append(PainterPathPlotItem(self.paths[0],pen=self.pen_down))
        view_items.append(PainterPathPlotItem(self.path,pen=self.pen_down))
        
        
        if self.device:
            # Also observe any change to job.media and job.device
            view_items.append(PainterPathPlotItem(self.device.path*t,pen=self.pen_media,skip_autorange=True))
            view_items.append(PainterPathPlotItem(self.device.padding_path*t,pen=self.pen_media_padding,skip_autorange=True))
        
        self.plot = view_items
        return view_items
    
    @observe('device.position')        
    def _position_changed(self,change):
        x0,y0,z0 = change['oldvalue']
        x1,y1,z1 = change['value']
        self.path.translate(x1-x0,y0-y1) # Reverse y
        self.plot[0].updateData(self.path)
        
    def stop(self):
        if self.device:
            self.device.close()
            
    def set_origin(self):
        pass
    
    def move_to_origin(self):
        x,y,z = self.device.position
        self.device.move(-x,-y,z)
    
    def move_up(self):
        x,y,z = self.device.position
        self.device.move(x,y+self.rate,z)
    
    def move_down(self):
        x,y,z = self.device.position
        self.device.move(x,y-self.rate,z)
    
    def move_left(self):
        x,y,z = self.device.position
        self.device.move(x-self.rate,y,z)
    
    def move_right(self):
        x,y,z = self.device.position
        self.device.move(x+self.rate,y,z)
    
    def toggle_trigger(self):
        x,y,z = self.device.position
        if z:
            z = 0
        else:
            z = 1
        self.device.move(x,y,z)