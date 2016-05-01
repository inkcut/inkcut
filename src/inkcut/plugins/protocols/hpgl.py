# -*- coding: utf-8 -*-
'''
Created on Jul 25, 2015

@author: jrm
'''
from inkcut.workbench.core.device import IDeviceProtocol

class HPGLProtocol(IDeviceProtocol):
    def connectionMade(self):
        self.write("IN;")
    
    def move(self,x,y,z):
        self.write("%s%i,%i;"%(z and "PD" or "PU",x,y))
        
    def setForce(self, f):
        self.write("FS%i;"%f)
        
    def setVelocity(self, v):
        self.write("VS%i;"%v)
        
    def setPen(self, p):
        self.write("SP%i;"%p)