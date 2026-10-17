# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

@author: jrm
"""
from atom.api import Instance, Bool, Enum
from inkcut.device.plugin import DeviceProtocol, Model
from inkcut.core.utils import log
from inkcut.core.svg import INKCUT_DPI
from inkcut.device.protocols.units import (
    ADDRESSING_LEGACY, ADDRESSING_ORDER, units_per_inch,
)


class HPGLConfig(Model):
    #: Pad option
    pad = Bool().tag(config=True)

    #: Whether use seperate PU/PD and PA or just PU/PD
    separate_z_moves = Bool().tag(config=True)

    addressing = Enum(*ADDRESSING_ORDER)(ADDRESSING_LEGACY).tag(config=True)

class HPGLProtocol(DeviceProtocol):
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
        per_inch = units_per_inch(self.config.addressing)
        x, y = int(x * per_inch / INKCUT_DPI), int(y * per_inch / INKCUT_DPI)
        if absolute:
            if self.config.separate_z_moves:
                self.write('PD;' if z else 'PU;')
                self.write("PA%i,%i;" % (x, y))
            else:
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

