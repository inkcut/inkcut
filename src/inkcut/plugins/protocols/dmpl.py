# -*- coding: utf-8 -*-
'''
Created on Jul 25, 2015

@author: jrm
'''
from inkcut.workbench.core.device import IDeviceProtocol

class DMPLProtocol(IDeviceProtocol):
    def connectionMade(self):
        self.write(" ;:H A L0 ")
    
    def move(self,x,y,z):
        self.write("%s%i,%i "%(z and "D" or "U",x,y))
        
    def setPen(self, p):
        self.write("EC%i "%p)
        
    def setVelocity(self, v):
        self.write("V%i "%v)
        
    def setForce(self, f):
        self.write("BP%i "%f)