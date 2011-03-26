#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
'''
This module includes the elements found in http://www.w3.org/TR/SVG/struct.html

(C) 2008, 2009 Kerim Mansour
For licensing information please refer to license.txt
'''
from attributes import *
from core import BaseElement, PointAttrib, DimensionAttrib


  
        
class g(BaseElement, CoreAttrib, ConditionalAttrib, StyleAttrib, ExternalAttrib, PresentationAttributes_All, GraphicalEventsAttrib):
    """
    Class representing the g element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'g')
        self.setKWARGS(**kwargs)
    
    def set_transform(self, transform):
        self._attributes['transform'] = transform
    def get_transform(self):
        return self._attributes.get('transform')   

class defs(g):
    """
    Class representing the defs element of an svg doc.
    """
    def __init__(self,**kwargs):
        BaseElement.__init__(self, 'defs')
        self.setKWARGS(**kwargs)


class desc(BaseElement, CoreAttrib, StyleAttrib):
    """
    Class representing the desc element of an svg doc.
    """
    def __init__(self,**kwargs):
        BaseElement.__init__(self, 'desc')
        self.setKWARGS(**kwargs)

class title(desc):
    """
    Class representing the title element of an svg doc.
    """
    def __init__(self,**kwargs):
        BaseElement.__init__(self, 'title')
        self.setKWARGS(**kwargs)

class metadata(BaseElement, CoreAttrib):
    """
    Class representing the metadata element of an svg doc.
    """
    def __init__(self,**kwargs):
        BaseElement.__init__(self, 'metadata')
        self.setKWARGS(**kwargs)

class symbol(BaseElement, CoreAttrib, StyleAttrib, ExternalAttrib, PresentationAttributes_All, GraphicalEventsAttrib):
    """
    Class representing the symbol element of an svg doc.
    """
    def __init__(self,**kwargs):
        BaseElement.__init__(self, 'symbol')
        self.setKWARGS(**kwargs)
    
    def set_viewBox(self, viewBox):
        self._attributes['viewBox'] = viewBox
    
    def get_viewBox(self):
        return self._attributes['viewBox']
    
    def set_preserveAspectRatio(self, preserveAspectRatio):
        self._attributes['preserveAspectRatio'] = preserveAspectRatio
    
    def get_preserveAspectRatio(self):
        return self._attributes['preserveAspectRatio']

class use(BaseElement, CoreAttrib, StyleAttrib, ConditionalAttrib, PointAttrib, DimensionAttrib, XLinkAttrib, PresentationAttributes_All, GraphicalEventsAttrib):
    """
    Class representing the use element of an svg doc.
    """
    def __init__(self,**kwargs):
        BaseElement.__init__(self, 'use')
        self.setKWARGS(**kwargs)

    def set_transform(self, transform):
        self._attributes['transform'] = transform
    def get_transform(self):
        return self._attributes.get('transform')

class svg(BaseElement, CoreAttrib, StyleAttrib, ConditionalAttrib, PointAttrib, DimensionAttrib, XLinkAttrib, PresentationAttributes_All, GraphicalEventsAttrib, DocumentEventsAttrib):
    """
    Class representing the svg element of an svg doc.
    """
    def __init__(self, x=None, y=None, width=None, height=None,**kwargs):
        BaseElement.__init__(self, 'svg')
        self.set_xmlns('http://www.w3.org/2000/svg')
        self.set_xmlns_xlink('http://www.w3.org/1999/xlink')
        self.set_version('1.1')
        self.set_x(x)
        self.set_y(y)
        self.set_height(height)
        self.set_width(width)
        self.setKWARGS(**kwargs)
        
    def set_version(self, version):
        self._attributes['version'] = version
    
    def get_version(self):
        return self._attributes['version']
    
    def set_xmlns(self, xmlns):
        self._attributes['xmlns'] = xmlns
    
    def get_xmlns(self):
        return self._attributes['xmlns']
    
    def set_xmlns_xlink(self, xmlns_xlink):
        self._attributes['xmlns:xlink'] = xmlns_xlink
    
    def get_xmlns_xlink(self):
        return self._attributes.get('xmlns:xlink')
        
    def set_viewBox(self, viewBox):
        self._attributes['viewBox'] = viewBox
    def get_viewBox(self):
        return self._attributes['viewBox']
    
    def set_preserveAspectRatio(self, preserveAspectRatio):
        self._attributes['preserveAspectRatio'] = preserveAspectRatio
    def get_preserveAspectRatio(self):
        return self._attributes['preserveAspectRatio']
    
    def set_transform(self, transform):
        self._attributes['transform'] = transform
    def get_transform(self):
        return self._attributes.get('transform') 
   
    def set_zoomAndPan(self, zoomAndPan):
        self._attributes['zoomAndPan'] = zoomAndPan
    def get_zoomAndPan(self):
        return self._attributes['zoomAndPan']
    
    def set_contentScriptType(self, contentScriptType):
        self._attributes['contentScriptType'] = contentScriptType
    def get_contentScriptType(self):
        return self._attributes['contentScriptType']
    
    def set_contentStyleType(self, contentStyleType):
        self._attributes['contentStyleType'] = contentStyleType
    def get_contentStyleType(self):
        return self._attributes['contentStyleType']  
    
    def set_baseProfile(self, baseProfile):
        self._attributes['baseProfile'] = baseProfile
    def get_baseProfile(self):
        return self._attributes['baseProfile']
#todo: check color.attrib and colorprofile.attrib. supposedly in image
class image(BaseElement, CoreAttrib, ConditionalAttrib, StyleAttrib, ViewportAttrib, PaintAttrib, OpacityAttrib, GraphicsAttrib, ClipAttrib, MaskAttrib, FilterAttrib, GraphicalEventsAttrib, CursorAttrib, XLinkAttrib, ExternalAttrib, PointAttrib, DimensionAttrib):
    """
    Class representing the image element of an svg doc.
    """
    def __init__(self, x=None, y=None, width=None, height=None, preserveAspectRatio=None,**kwargs):
        BaseElement.__init__(self, 'image')
        self.set_x(x)
        self.set_y(y)
        self.set_height(height)
        self.set_width(width)
        self.set_preserveAspectRatio(preserveAspectRatio)
        self.setKWARGS(**kwargs)
    
    #def set_embedded(self,embedded):
    #    self._attributes['embedded']=embedded
        
    def set_preserveAspectRatio(self, preserveAspectRatio):
        self._attributes['preserveAspectRatio'] = preserveAspectRatio
    def get_preserveAspectRatio(self):
        return self._attributes['preserveAspectRatio']
    
    def set_transform(self, transform):
        self._attributes['transform'] = transform
    def get_transform(self):
        return self._attributes.get('transform') 

class switch(BaseElement, CoreAttrib, ConditionalAttrib, StyleAttrib, PresentationAttributes_All, GraphicalEventsAttrib, ExternalAttrib):
    """
    Class representing the switch element of an svg doc.
    """
    def __init__(self,**kwargs):
        BaseElement.__init__(self, 'switch')
        self.setKWARGS(**kwargs)
        
    def set_transform(self, transform):
        self._attributes['transform'] = transform
    def get_transform(self):
        return self._attributes.get('transform') 

class clipPath(BaseElement, CoreAttrib, ConditionalAttrib, StyleAttrib, ExternalAttrib, PresentationAttributes_All, GraphicalEventsAttrib):
    """
    Class representing the clipPath element of an svg doc.
    """
    def __init__(self, id=None, transform=None, clipPathUnits=None,**kwargs):
        BaseElement.__init__(self, 'clipPath')
        self.set_id(id)
        self.set_transform(transform)
        self.set_clipPathUnits(clipPathUnits)
        self.setKWARGS(**kwargs)
        
    
    def set_transform(self, transform):
        self._attributes['transform'] = transform
    def get_transform(self):
        return self._attributes.get('transform') 
    
    def set_clipPathUnits(self, clipPathUnits):
        self._attributes['clipPathUnits'] = clipPathUnits
        
    def get_clipPathUnits(self):
        return self._attributes['clipPathUnits']
