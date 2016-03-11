# -*- coding: utf-8 -*-
'''
Created on Jul 25, 2015

@author: jrm
'''
from inkcut.workbench.core.device import IDeviceProtocol

class DMPLProtocol(IDeviceProtocol):
    def init(self):
        self.write(" ;:H A L0 ")
    
    def move(self,x,y,z):
        self.write("%s%i,%i "%(z and "D" or "U",x,y))
        
    def set_pen(self, p):
        self.write("EC%i "%p)
        
    def set_velocity(self, v):
        self.write("V%i "%v)
        
    def set_force(self, f):
        self.write("BP%i "%f)