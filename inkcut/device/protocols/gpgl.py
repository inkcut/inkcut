# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

Thanks to Lex Wernars

@author: jrm
@author: lwernars
"""
from inkcut.device.plugin import DeviceProtocol


class GPGLProtocol(DeviceProtocol):
    def connection_made(self):
        self.write("H")

    def move(self, x, y, z, absolute=True):
        self.write("%s%i,%i"%('D' if z else 'M', x, y))

    def set_velocity(self, v):
        self.write('!%i' % v)

    def set_force(self, f):
        self.write("FX%i,1" % f)

    def set_pen(self, p):
        pass
