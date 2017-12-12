# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

@author: jrm
"""
from inkcut.device.plugin import DeviceProtocol


class DMPLProtocol(DeviceProtocol):

    def connection_made(self):
        self.write(" ;:H A L0 ")
    
    def move(self, x, y, z):
        self.write("{z}{x},{y} ".format(x=x, y=y, z=z and "D" or "U"))
        
    def set_pen(self, p):
        self.write("EC{p} ".format(p=p))
        
    def set_velocity(self, v):
        self.write("V{v} ".format(v=v))
        
    def set_force(self, f):
        self.write("BP{f} ".format(f=f))

    def connection_lost(self):
        pass