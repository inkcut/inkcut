#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
'''
(C) 2008, 2009 Kerim Mansour
For licensing information please refer to license.txt
'''
from attributes import *
from core import BaseElement

  
        
class a(BaseElement, CoreAttrib, ConditionalAttrib, StyleAttrib, ExternalAttrib, PresentationAttributes_All, GraphicalEventsAttrib, XLinkAttrib):
    """
    Class representing the a element of an svg doc.
    """
    def __init__(self, target=None):
        BaseElement.__init__(self,'a')
        self.set_target(target)
        
    def set_transform(self, transform):
        self._attributes['transform']=transform
    def get_transform(self):
        return self._attributes.get('transform')
    
    def set_target(self, target):
        self._attributes['target']=target
    def get_target(self):
        return self._attributes.get('target')

class view(BaseElement, CoreAttrib, ExternalAttrib):
    """
    Class representing the view element of an svg doc.
    """
    def __init__(self, ):
        BaseElement.__init__(self,'view')
    
    def set_transform(self, transform):
        self._attributes['transform']=transform
    def get_transform(self):
        return self._attributes.get('transform')
    
    def set_target(self, target):
        self._attributes['target']=target
    def get_target(self):
        return self._attributes.get('target')
    
    def set_viewBox(self,viewBox):
        self._attributes['viewBox']=viewBox
    
    def get_viewBox(self):
        return self._attributes['viewBox']
    
    def set_preserveAspectRatio(self,preserveAspectRatio):
        self._attributes['preserveAspectRatio']=preserveAspectRatio
    
    def get_preserveAspectRatio(self):
        return self._attributes['preserveAspectRatio']
    
    def set_zoomAndPan(self,zoomAndPan):
        self._attributes['zoomAndPan']=zoomAndPan
    def get_zoomAndPan(self):
        return self._attributes['zoomAndPan']
    
    def set_viewTarget(self,viewTarget):
        self._attributes['viewTarget']=viewTarget
    def get_viewTarget(self):
        return self._attributes['viewTarget']