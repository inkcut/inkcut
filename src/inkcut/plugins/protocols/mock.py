# -*- coding: utf-8 -*-
'''
Created on Oct 23, 2015

@author: jrm
'''
from inkcut.workbench.core.device import IDeviceProtocol

class MockProtocol(IDeviceProtocol):
    """ Just log what is called """
    def init(self):
        self.log.debug("protocol.init()")
    
    def move(self,x,y,z):
        self.log.debug("protocol.move({0},{1},{2})".format(x,y,z))
        
    def set_pen(self, p):
        self.log.debug("protocol.set_pen({0})".format(p))
        
    def set_velocity(self, v):
        self.log.debug("protocol.set_force({0})".format(v))
        
    def set_force(self, f):
        self.log.debug("protocol.set_force({0})".format(f))