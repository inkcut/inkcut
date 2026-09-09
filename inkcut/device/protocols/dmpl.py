# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

Thanks to Lex Wernars

@author: jrm
@author: lwernars
"""
from atom.api import Enum, Instance, Float
from inkcut.device.plugin import DeviceProtocol, Model
from inkcut.core.svg import INKCUT_DPI

class DMPLConfig(Model):
    #: Version number
    mode = Enum(1, 2, 3, 4, 6).tag(config=True)


class DMPLProtocol(DeviceProtocol):

    #: Different modes
    config = Instance(DMPLConfig, ()).tag(config=True)

    #: Output scaling
    scale = Float(1021/INKCUT_DPI)

    async def init(self):
        v = self.config.mode
        if v == 1:
            await self.write(";:HAEC1")
        elif v == 2:
            await self.write(" ;:ECN A L0 ")
        elif v in [3, 4]:
            await self.write(" ;:H A L0 ")
        elif v == 6:
            await self.write("IN;PA;")

    async def move(self, x, y, z, absolute=True):
        x, y = int(x*self.scale), int(y*self.scale)
        v = self.config.mode
        if v in [1, 2, 3, 4]:
            await self.write(" {z}{x},{y} ".format(x=x, y=y, z=z and "D" or "U"))
        else:
            await self.write("{z}{x},{y};".format(x=x, y=y, z=z and "PD" or "PU"))

    async def set_pen(self, p):
        await self.write("EC{p} ".format(p=p))

    async def set_velocity(self, v):
        await self.write("V{v} ".format(v=v))

    async def set_force(self, f):
        await self.write("BP{f} ".format(f=f))
