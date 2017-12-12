# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

Thanks to Lex Wernars

@author: jrm
@author: lwernars
"""
from atom.api import Enum, Instance
from inkcut.device.plugin import DeviceProtocol, Model


class DMPLConfig(Model):
    #: Version number
    mode = Enum(1, 2, 3, 4, 6).tag(config=True)


class DMPLProtocol(DeviceProtocol):

    #: Different modes
    config = Instance(DMPLConfig, ()).tag(config=True)

    def connection_made(self):
        v = self.config.mode
        if v == 1:
            self.write(";:HAEC1")
        elif v == 2:
            self.write(" ;:ECN A L0 ")
        elif v in [3, 4]:
            self.write(" ;:H A L0 ")
        elif v == 6:
            self.write("IN;PA;")

    def move(self, x, y, z):
        v = self.config.mode
        if v in [1, 2, 3, 4]:
            self.write(" {z}{x},{y} ".format(x=x, y=y, z=z and "D" or "U"))
        else:
            self.write("{z}{x},{y};".format(x=x, y=y, z=z and "PD" or "PU"))
        
    def set_pen(self, p):
        self.write("EC{p} ".format(p=p))
        
    def set_velocity(self, v):
        self.write("V{v} ".format(v=v))
        
    def set_force(self, f):
        self.write("BP{f} ".format(f=f))

    def connection_lost(self):
        pass