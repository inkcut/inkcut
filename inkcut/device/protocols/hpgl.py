# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

@author: jrm
"""
from atom.api import Instance, Float, Bool, Int
from inkcut.device.plugin import DeviceProtocol, Model
from inkcut.core.utils import log


class HPGLConfig(Model):
    #: Pad option
    pad = Bool().tag(config=True)


class HPGLProtocol(DeviceProtocol):
    scale = Float(1021/90.0)

    #: Pad option
    config = Instance(HPGLConfig, ()).tag(config=True)

    def write(self, data):
        if self.config.pad:
            data += "\n"
        super().write(data)

    def connection_made(self):
        #: Initialize in absoulte mode
        self.write("IN;")

    def move(self, x, y, z, absolute=True):
        """ Move the given position. If absolute is true use a PR
        otherwise use PA. Most of the chinese machines don't handle
        negative values so absolute moves only works.
        
        """
        x, y = int(x*self.scale), int(y*self.scale)
        if absolute:
            self.write("%s%i,%i;" % ('PD' if z else 'PU', x, y))
        else:
            self.write('PR%i,%i;' % (x, y))

    def set_force(self, f):
        self.write("FS%i; " % f)
        
    def set_velocity(self, v):
        self.write("VS%i;" % v)
        
    def set_pen(self, p):
        self.write("SP%i;" % p)
        
    def finish(self):
        # Reinitialize
        self.write("IN;")

