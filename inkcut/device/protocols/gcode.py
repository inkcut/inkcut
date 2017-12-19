# -*- coding: utf-8 -*-
"""
Created on Dec 30, 2016

@author: jrm
"""
from inkcut.device.plugin import DeviceProtocol


class GCodeProtocol(DeviceProtocol):

    def connection_made(self):
        self.write("G28; Return to home\n")
        self.write("G98; Return to initial z\n")
        self.write("G90; Use absolute coordinates\n")
    
    def move(self, x, y, z, absolute=True):
        self.write("G0%i X%i Y%i;\n" % (z, x, y))
        
    def set_force(self, f):
        raise NotImplementedError
        
    def set_velocity(self, v):
        raise NotImplementedError
        
    def set_pen(self, p):
        raise NotImplementedError

    def finish(self):
        self.write("G28; Return to home\n")
        self.write("G98; Return to initial z\n")

    def connection_lost(self):
        pass