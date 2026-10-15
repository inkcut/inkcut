# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

Thanks to Lex Wernars

@author: jrm
@author: lwernars
"""
from atom.api import Bool, Enum, Instance, Float
from inkcut.device.plugin import DeviceProtocol, Model
from inkcut.core.svg import INKCUT_DPI

class DMPLConfig(Model):
    #: Version number
    mode = Enum(1, 2, 3, 4, 6).tag(config=True)

    #: Some firmwares (e.g. the Anhui-Anyu boards in VEVOR cutters)
    #: transpose the DMPL axes: the first coordinate drives the media
    #: feed rollers and the second the carriage. Emitting (y, x) restores
    #: Inkcut's convention (y = feed) so feed-to-end, pre-feed and the
    #: origin bookkeeping act on the rollers, not the carriage.
    swap_axes = Bool().tag(config=True)


class DMPLProtocol(DeviceProtocol):

    #: Different modes
    config = Instance(DMPLConfig, ()).tag(config=True)

    #: Output scaling. DMPL standard resolution is 0.025 mm per step =
    #: 1016 steps/inch (confirmed for the Vevor KH-870 D-type mainboard by
    #: the manufacturer's driver data); the previous 1021 was ~0.5% off.
    scale = Float(1016/INKCUT_DPI)

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
        x, y = int(x*self.scale), int(y*self.scale)
        if self.config.swap_axes:
            x, y = y, x
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
