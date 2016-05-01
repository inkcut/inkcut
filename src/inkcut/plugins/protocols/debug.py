# -*- coding: utf-8 -*-
'''
Created on Oct 23, 2015

@author: jrm
'''
from inkcut.workbench.core.device import IDeviceProtocol

class DebugProtocol(IDeviceProtocol):
    """ Just log what is called """
    def connectionMade(self):
        self.log.debug("protocol.init()")
    
    def move(self,x,y,z):
        self.log.debug("protocol.move({0},{1},{2})".format(x,y,z))
        
    def setPen(self, p):
        self.log.debug("protocol.setPen({0})".format(p))
        
    def setVelocity(self, v):
        self.log.debug("protocol.setVelocity({0})".format(v))
        
    def setForce(self, f):
        self.log.debug("protocol.setForce({0})".format(f))