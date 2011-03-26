#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
'''
(C) 2008, 2009 Kerim Mansour
For licensing information please refer to license.txt
'''
from attributes import *
from core import BaseElement, PointAttrib, DeltaPointAttrib, RotateAttrib

class altGlyphDef(BaseElement, CoreAttrib):
    """
    Class representing the altGlyphDef element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'altGlypfDef')
        self.setKWARGS(**kwargs)
        
class altGlyphItem(BaseElement, CoreAttrib):
    """
    Class representing the altGlyphItem element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'altGlypfItem')
        self.setKWARGS(**kwargs)

class glyphRef(BaseElement, CoreAttrib, ExternalAttrib, StyleAttrib, FontAttrib, XLinkAttrib, PaintAttrib, PointAttrib, DeltaPointAttrib):
    """
    Class representing the glyphRef element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'glyphRef')
        self.setKWARGS(**kwargs)
    
    def set_glyphRef(self, glyphRef):
        self._attributes['glyphRef'] = glyphRef
    def get_glyphRef(self):
        return self._attributes.get('glyphRef')
    
    def set_format(self, format):
        self._attributes['format'] = format
    def get_format(self):
        return self._attributes.get('format')
    
    def set_lengthAdjust(self, lengthAdjust):
        self._attributes['lengthAdjust'] = lengthAdjust
    def get_lengthAdjust(self):
        return self._attributes.get('lengthAdjust')

class altGlyph(glyphRef, ConditionalAttrib, GraphicalEventsAttrib, OpacityAttrib, GraphicsAttrib, CursorAttrib, FilterAttrib, MaskAttrib, ClipAttrib, TextContentAttrib, RotateAttrib):
    """
    Class representing the altGlyph element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'altGlyph')
        self.setKWARGS(**kwargs)
    
    def set_textLength(self, textLength):
        self._attributes['textLength'] = textLength
    def get_textLength(self):
        return self._attributes.get('textLength')

class textPath(BaseElement, CoreAttrib, ConditionalAttrib, ExternalAttrib, StyleAttrib, XLinkAttrib, FontAttrib, PaintAttrib, GraphicalEventsAttrib, OpacityAttrib, GraphicsAttrib, CursorAttrib, FilterAttrib, MaskAttrib, ClipAttrib, TextContentAttrib):
    """
    Class representing the textPath element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'textPath')
        self.setKWARGS(**kwargs)
    
    def set_startOffset(self, startOffset):
        self._attributes['startOffset'] = startOffset
    def get_startOffset(self):
        return self._attributes.get('startOffset')
    
    def set_textLength(self, textLength):
        self._attributes['textLength'] = textLength
    def get_textLength(self):
        return self._attributes.get('textLength')
    
    def set_lengthAdjust(self, lengthAdjust):
        self._attributes['lengthAdjust'] = lengthAdjust
    def get_lengthAdjust(self):
        return self._attributes.get('lengthAdjust')
    
    def set_method(self, method):
        self._attributes['method'] = method
    def get_method(self):
        return self._attributes.get('method')
    
    def set_spacing(self, spacing):
        self._attributes['spacing'] = spacing
    def get_spacing(self):
        return self._attributes.get('spacing')

class tref(BaseElement, CoreAttrib, ConditionalAttrib, ExternalAttrib, StyleAttrib, XLinkAttrib, PointAttrib, DeltaPointAttrib, RotateAttrib, GraphicalEventsAttrib, PaintAttrib, FontAttrib, OpacityAttrib, GraphicsAttrib, CursorAttrib, FilterAttrib, MaskAttrib, ClipAttrib, TextContentAttrib):
    """
    Class representing the tref element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self, 'tref')
        self.setKWARGS(**kwargs)
    
    def set_textLength(self, textLength):
        self._attributes['textLength'] = textLength
    def get_textLength(self):
        return self._attributes.get('textLength')
    
    def set_lengthAdjust(self, lengthAdjust):
        self._attributes['lengthAdjust'] = lengthAdjust
    def get_lengthAdjust(self):
        return self._attributes.get('lengthAdjust')

class tspan(BaseElement, CoreAttrib, ConditionalAttrib, ExternalAttrib, StyleAttrib, PointAttrib, DeltaPointAttrib, RotateAttrib, GraphicalEventsAttrib, PaintAttrib, FontAttrib, OpacityAttrib, GraphicsAttrib, CursorAttrib, FilterAttrib, MaskAttrib, ClipAttrib, TextContentAttrib):
    """
    Class representing the tspan element of an svg doc.
    """
    def __init__(self, x=None, y=None, dx=None, dy=None, rotate=None, textLength=None, lengthAdjust=None, **kwargs):
        BaseElement.__init__(self, 'tspan')
        self.set_x(x)
        self.set_y(y)
        self.set_dx(dx)
        self.set_dy(dy)
        self.set_rotate(rotate)
        self.set_textLength(textLength)
        self.set_lengthAdjust(lengthAdjust)
        self.setKWARGS(**kwargs)
        
    def set_textLength(self, textLength):
        self._attributes['textLength'] = textLength
    def get_textLength(self):
        return self._attributes.get('textLength')
    
    def set_lengthAdjust(self, lengthAdjust):
        self._attributes['lengthAdjust'] = lengthAdjust
    def get_lengthAdjust(self):
        return self._attributes.get('lengthAdjust')
    
class text(BaseElement, CoreAttrib, ConditionalAttrib, ExternalAttrib, StyleAttrib, PointAttrib, DeltaPointAttrib, RotateAttrib, GraphicalEventsAttrib, PaintAttrib, FontAttrib, OpacityAttrib, GraphicsAttrib, CursorAttrib, FilterAttrib, MaskAttrib, ClipAttrib, TextContentAttrib, TextAttrib):
    """
    Class representing the text element of an svg doc.
    """
    def __init__(self, content=None, x=None, y=None, dx=None, dy=None, rotate=None, textLength=None, lengthAdjust=None, **kwargs):
        BaseElement.__init__(self, 'text')
        if content <> None:
            self.appendTextContent(content)
        self.set_x(x)
        self.set_y(y)
        self.set_dx(dx)
        self.set_dy(dy)
        self.set_rotate(rotate)
        self.set_textLength(textLength)
        self.set_lengthAdjust(lengthAdjust)
        self.setKWARGS(**kwargs)
        
    def set_transform(self, transform):
        self._attributes['transform'] = transform
    def get_transform(self):
        return self._attributes.get('transform')   
    
    def set_textLength(self, textLength):
        self._attributes['textLength'] = textLength
    def get_textLength(self):
        return self._attributes.get('textLength')
    
    def set_lengthAdjust(self, lengthAdjust):
        self._attributes['lengthAdjust'] = lengthAdjust
    def get_lengthAdjust(self):
        return self._attributes.get('lengthAdjust')
    
