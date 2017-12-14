# -*- coding: utf-8 -*-
"""
Created on Dec 30, 2016

@author: jrm
"""
from inkcut.device.plugin import DeviceProtocol


class CAMMGL1Protocol(DeviceProtocol):
    def connection_made(self):
        self.write("IN;")
    
    def move(self, x, y, z, absolute=True):
        self.write("{z}{x},{y};".format(x=x, y=y, z=z and "D" or "M", ))
        
    def set_force(self, f):
        self.write("FS{f};".format(f=f))
        
    def set_velocity(self, v):
        self.write("VS{v};".format(v=v))
        
    def set_pen(self, p):
        self.write("SP{p};".format(p=p))

    def connection_lost(self):
        pass
