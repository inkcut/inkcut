# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

@author: jrm
"""
from atom.api import Float
from inkcut.device.plugin import DeviceProtocol
from inkcut.core.utils import log


class HPGLProtocol(DeviceProtocol):
    scale = Float(1021/90.0)

    def connection_made(self):
        self.write("IN;")

    # def init(self, job):
    #     #: Rotate 90 deg
    #     #job.model.rotation = 90
    #     #job.model.scale = 1021/90.0

    def move(self, x, y, z, absolute=True):
        #: Swap x and y to rotate 90 deg
        y, x = int(x*self.scale), int(y*self.scale)
        if absolute:
            #: Force coords to be positive
            x, y = max(0, x), max(0, y)
            self.write("%s%i,%i;" % (z and "PD" or "PU", x, y))
        else:
            self.write("PR%i,%i;" % (x, y))

    def set_force(self, f):
        self.write("FS%i; " % f)
        
    def set_velocity(self, v):
        self.write("VS%i;" % v)
        
    def set_pen(self, p):
        self.write("SP%i;" % p)

