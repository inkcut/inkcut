# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

@author: jrm
"""
from atom.api import Float
from inkcut.device.plugin import DeviceProtocol


class HPGLProtocol(DeviceProtocol):
    scale = Float(1021/90.0)

    def connection_made(self):
        self.write("IN;")

    # def init(self, job):
    #     #: Rotate 90 deg
    #     #job.model.rotation = 90
    #     #job.model.scale = 1021/90.0

    def move(self, x, y, z):
        #: Swap x and y to rotate 90 deg
        y, x = int(x*self.scale), int(y*self.scale)
        self.write("%s%i,%i;" % (z and "PD" or "PU", x, y))
        
    def set_force(self, f):
        self.write("FS%i; " % f)
        
    def set_velocity(self, v):
        self.write("VS%i;" % v)
        
    def set_pen(self, p):
        self.write("SP%i;" % p)

    def finish(self):
        self.write("PU0,0;")
