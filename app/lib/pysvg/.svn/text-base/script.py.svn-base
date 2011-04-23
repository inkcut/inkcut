#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
'''
(C) 2008, 2009 Kerim Mansour
For licensing information please refer to license.txt
'''
from attributes import CoreAttrib, XLinkAttrib
from core import BaseElement

  
         
class script(BaseElement, CoreAttrib, XLinkAttrib):
    """
    Class representing the script element of an svg doc.
    """
    def __init__(self, **kwargs):
        BaseElement.__init__(self,'script')
        self.setKWARGS(**kwargs)
    
    def set_type(self, type):
        self._attributes['type']=type
    def get_type(self):
        return self._attributes.get('type')
