# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

@author: jrm
"""
from atom.api import Float, Bool, Int
from inkcut.device.plugin import DeviceProtocol
from inkcut.core.utils import log


class HPGLProtocol(DeviceProtocol):
    scale = Float(1021/90.0)
    #absolute = Bool(True)
    z = Int(0)

    def connection_made(self):
        #: Initialize in absoulte mode
        self.write("IN;")

        #: Reset state
        #self.absolute = True
        self.z = 0

    def move(self, x, y, z, absolute=True):
        """ Move the given position. If absolute is true use a PR
        otherwise use PA. Most of the chinese machines don't handle
        negative values so absolute moves only works.
        
        """
        x, y = int(x*self.scale), int(y*self.scale)
        self.z = z
        #self.absolute = absolute
        if absolute:
            self.write("PA%i,%i;" % (x, y))
        else:
            self.write('PR%i,%i;' % (x, y))

    def _observe_z(self, change):
        self.write("%s;" % ('PD' if self.z else 'PU',))

    #def _observe_absolute(self, change):
    #    self.write("%s;" % ('PA' if self.absolute else 'PR',))

    def set_force(self, f):
        self.write("FS%i; " % f)
        
    def set_velocity(self, v):
        self.write("VS%i;" % v)
        
    def set_pen(self, p):
        self.write("SP%i;" % p)

