# -*- coding: utf-8 -*-
'''
Created on Jul 20, 2015

@author: jrm
'''
from atom.api import observe,ContainerList,Float,Instance
from inkcut.workbench.core.utils import ConfigurableAtom
from enaml.qt import QtCore,QtGui

class AreaBase(ConfigurableAtom):
    
    size = ContainerList(Float(),default=[1800,2700]).tag(config=True)
    padding = ContainerList(Float(),default=[10,10,10,10]).tag(config=True) # Left, Top, Right, Bottom
    area = Instance(QtCore.QRectF)
    path = Instance(QtGui.QPainterPath)
    padding_path = Instance(QtGui.QPainterPath)
    
    def _default_area(self):
        return QtCore.QRectF(0,0,self.size[0],self.size[1])
    
    def _default_path(self):
        p = QtGui.QPainterPath()
        p.addRect(self.area)
        return p
    
    def _default_padding_path(self):
        p = QtGui.QPainterPath()
        p.addRect(self.available_area)
        return p
        
    @observe('size','padding')
    def _sync_size(self,change):
        self.area.setWidth(self.size[0])
        self.area.setHeight(self.size[1])
        self.path = self._default_path()
        self.padding_path = self._default_path()
        
    @property
    def padding_left(self):
        return self.padding[0]
    
    @property
    def padding_top(self):
        return self.padding[1]
    
    @property
    def padding_right(self):
        return self.padding[2]
    
    @property
    def padding_bottom(self):
        return self.padding[3]
        
    def width(self):
        return self.size[0]
    
    def height(self):
        return self.size[1]
    
    @property
    def available_area(self):
        x,y = self.padding_left,self.padding_bottom
        w,h = self.size[0]-(self.padding_right+self.padding_left),self.size[1]-(self.padding_bottom+self.padding_top)
        return QtCore.QRectF(x,y,w,h)
        
    