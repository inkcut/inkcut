# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

Thanks to Lex Wernars

@author: jrm
@author: lwernars
"""
from atom.api import Enum, Instance
from inkcut.device.plugin import DeviceProtocol, Model
from inkcut.core.svg import INKCUT_DPI
from inkcut.device.protocols.units import (
    ADDRESSING_0_001_INCH, ADDRESSING_0_025_MM, ADDRESSING_LEGACY,
    ADDRESSING_ORDER, units_per_inch,
)

class DMPLConfig(Model):
    #: Version number
    mode = Enum(1, 2, 3, 4, 6).tag(config=True)

    #: Modes 3, 4, and 6. Modes 1 and 2 send the unit on connect.
    addressing = Enum(*ADDRESSING_ORDER)(ADDRESSING_LEGACY).tag(config=True)


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

    def move(self, x, y, z, absolute=True):
        mode = self.config.mode
        if mode == 1:
            per_inch = units_per_inch(ADDRESSING_0_001_INCH)
        elif mode == 2:
            per_inch = units_per_inch(ADDRESSING_0_025_MM)
        else:
            # Modes 3, 4, and 6. Connect does not set a unit.
            per_inch = units_per_inch(self.config.addressing)
        x, y = int(x * per_inch / INKCUT_DPI), int(y * per_inch / INKCUT_DPI)
        if mode in [1, 2, 3, 4]:
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
