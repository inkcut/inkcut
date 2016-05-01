# -*- coding: utf-8 -*-
'''
Created on Jul 25, 2015

@author: jrm
'''
from inkcut.workbench.core.device import IDeviceProtocol

class GPGLProtocol(IDeviceProtocol):
    def connectionMade(self):
        self.write("H")
        
    def move(self,x,y,z):
        self.write("%s%i,%i;"%(z and "M" or "D",x,y))
        
    def setVelocity(self, v):
        self.write("!%i"%v)
        
    def setForce(self, f):
        self.write("*%i"%f)
    