# -*- coding: utf-8 -*-
'''
Created on Jul 25, 2015

@author: jrm
'''
from atom.api import Float
from inkcut.workbench.core.device import IDeviceProtocol


class HPGLProtocol(IDeviceProtocol):
    scale = Float(1021/90.0)

    def connectionMade(self):
        self.write("IN;")

    # def init(self, job):
    #     #: Rotate 90 deg
    #     #job.model.rotation = 90
    #     #job.model.scale = 1021/90.0

    def move(self, x, y, z):
        #: Swap x and y to rotate 90 deg
        y,x = int(x*self.scale), int(y*self.scale)
        self.write("%s%i,%i;"%(z and "PD" or "PU", x, y))
        
    def setForce(self, f):
        self.write("FS%i; "%f)
        
    def setVelocity(self, v):
        self.write("VS%i;"%v)
        
    def setPen(self, p):
        self.write("SP%i;"%p)

    def finish(self):
        self.write("PU0,0;")
