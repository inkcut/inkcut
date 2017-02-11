# -*- coding: utf-8 -*-
'''
Created on Dec 30, 2016

@author: jrm
'''
from inkcut.workbench.core.device import IDeviceProtocol

class GCodeProtocol(IDeviceProtocol):
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