# -*- coding: utf-8 -*-
"""
Created on Dec 30, 2016

@author: jrm
"""
from inkcut.device.plugin import DeviceProtocol


class GCodeProtocol(DeviceProtocol):

    def connection_made(self):
        self.write("IN;")
    
    def move(self, x, y, z):
        self.write("%s%i,%i;"%(z and "PD" or "PU", x, y))
        
    def set_force(self, f):
        self.write("FS%i;"%f)
        
    def set_velocity(self, v):
        self.write("VS%i;"%v)
        
    def set_pen(self, p):
        self.write("SP%i;"%p)

    def connection_lost(self):
        pass