#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
'''
(C) 2008, 2009 Kerim Mansour
For licensing information please refer to license.txt
'''
from attributes import *
from core import BaseElement, PointAttrib, DimensionAttrib

  
        
class linearGradient(BaseElement, CoreAttrib, XLinkAttrib, PaintAttrib, StyleAttrib, ExternalAttrib):
    """
    Class representing the linearGradient element of an svg doc.
    """
    def __init__(self, x1=None, y1=None, x2=None, y2=None, **kwargs):
        BaseElement.__init__(self, 'linearGradient')
        self.set_x1(x1)
        self.set_y1(y1)
        self.set_x2(x2)
        self.set_y2(y2)
        self.setKWARGS(**kwargs)
    
    def set_x1(self, x1):
        self._attributes['x1'] = x1
    def get_x1(self):
        return self._attributes.get('x1')
    
    def set_y1(self, y1):
        self._attributes['y1'] = y1
    def get_y1(self):
        return self._attributes.get('y1')
    
    def set_x2(self, x2):
        self._attributes['x2'] = x2
    def get_x2(self):
        return self._attributes.get('x2')
    
    def set_y2(self, y2):
        self._attributes['y2'] = y2
    def get_y2(self):
        return self._attributes.get('y2')
    
    def set_gradientUnits(self, gradientUnits):
        self._attributes['gradientUnits'] = gradientUnits
    def get_gradientUnits(self):
        return self._attributes.get('gradientUnits')
    
    def set_gradientTransform(self, gradientTransform):
        self._attributes['gradientTransform'] = gradientTransform
    def get_gradientTransform(self):
        return self._attributes.get('gradientTransform')
    
    def set_spreadMethod(self, spreadMethod):
        self._attributes['spreadMethod'] = spreadMethod
    def get_spreadMethod(self):
        return self._attributes.get('spreadMethod')
    
class radialGradient(BaseElement, CoreAttrib, XLinkAttrib, PaintAttrib, StyleAttrib, ExternalAttrib):
    """
    Class representing the radialGradient element of an svg doc.
    """
    def __init__(self, cx='50%', cy='50%', r='50%', fx='50%', fy='50%', **kwargs):
        BaseElement.__init__(self, 'radialGradient')
        self.set_cx(cx)
        self.set_cy(cy)
        self.set_fx(fx)
        self.set_fy(fy)
        self.set_r(r)
        self.setKWARGS(**kwargs)
        
    def set_cx(self, cx):
        self._attributes['cx'] = cx
    def get_cx(self):
        return self._attributes.get('cx')
    
    def set_cy(self, cy):
        self._attributes['cy'] = cy
    def get_cy(self):
        return self._attributes.get('cy')
    
    def set_r(self, r):
        self._attributes['r'] = r
    def get_r(self):
        return self._attributes.get('r')
    
    def set_fx(self, fx):
        self._attributes['fx'] = fx
    def get_fx(self):
        return self._attributes.get('fx')
    
    def set_fy(self, fy):
        self._attributes['fy'] = fy
    def get_fy(self):
        return self._attributes.get('fy')
    
    def set_gradientUnits(self, gradientUnits):
        self._attributes['gradientUnits'] = gradientUnits
    def get_gradientUnits(self):
        return self._attributes.get('gradientUnits')
    
    def set_gradientTransform(self, gradientTransform):
        self._attributes['gradientTransform'] = gradientTransform
    def get_gradientTransform(self):
        return self._attributes.get('gradientTransform')
    
    def set_spreadMethod(self, spreadMethod):
        self._attributes['spreadMethod'] = spreadMethod
    def get_spreadMethod(self):
        return self._attributes.get('spreadMethod')    
    
class stop(BaseElement, CoreAttrib, StyleAttrib, PaintAttrib, GradientAttrib):
    """
    Class representing the stop element of an svg doc.
    """
    def __init__(self, offset=None, **kwargs):
        BaseElement.__init__(self, 'stop')
        self.set_offset(offset)
        self.setKWARGS(**kwargs)
        
    def set_offset(self, offset):
        self._attributes['offset'] = offset
    def get_offset(self):
        return self._attributes.get('offset')    

class pattern(BaseElement, CoreAttrib, XLinkAttrib, ConditionalAttrib, ExternalAttrib, StyleAttrib, PresentationAttributes_All, PointAttrib, DimensionAttrib):
    """
    Class representing the pattern element of an svg doc.
    """
    def __init__(self, x=None, y=None, width=None, height=None, patternUnits=None, patternContentUnits=None, patternTransform=None, viewBox=None, preserveAspectRatio=None, **kwargs):
        BaseElement.__init__(self, 'pattern')
        self.set_x(x)
        self.set_y(y)
        self.set_width(width)
        self.set_height(height)
        self.set_patternUnits(patternUnits)
        self.set_patternContentUnits(patternContentUnits)
        self.set_patternTransform(patternTransform)
        self.set_viewBox(viewBox)
        self.set_preserveAspectRatio(preserveAspectRatio)
        self.setKWARGS(**kwargs)
        
    def set_viewBox(self, viewBox):
        self._attributes['viewBox'] = viewBox
    
    def get_viewBox(self):
        return self._attributes['viewBox']
    
    def set_preserveAspectRatio(self, preserveAspectRatio):
        self._attributes['preserveAspectRatio'] = preserveAspectRatio
    
    def get_preserveAspectRatio(self):
        return self._attributes['preserveAspectRatio']
    
    def set_patternUnits(self, patternUnits):
        self._attributes['patternUnits'] = patternUnits
    
    def get_patternUnits(self):
        return self._attributes['patternUnits']
    
    def set_patternContentUnits(self, patternContentUnits):
        self._attributes['patternContentUnits'] = patternContentUnits
    def get_patternContentUnits(self):
        return self._attributes['patternContentUnits']
    
    def set_patternTransform(self, patternTransform):
        self._attributes['patternTransform'] = patternTransform
    
    def get_patternTransform(self):
        return self._attributes['patternTransform']
