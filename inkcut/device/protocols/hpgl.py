# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

@author: jrm
"""
from atom.api import Instance, Float, Bool, Int
from inkcut.device.plugin import DeviceProtocol, Model
from inkcut.core.utils import log
from inkcut.core.svg import INKCUT_DPI


class HPGLConfig(Model):
    #: Pad option
    pad = Bool().tag(config=True)

    #: Whether use seperate PU/PD and PA or just PU/PD
    separate_z_moves = Bool().tag(config=True)

class HPGLProtocol(DeviceProtocol):
    scale = Float(1021/INKCUT_DPI)

    #: Pad option
    config = Instance(HPGLConfig, ()).tag(config=True)

    async def write(self, data):
        if self.config.pad:
            data += "\n"
        await super().write(data)

    async def init(self):
        #: Initialize in absoulte mode
        await self.write("IN;")

    async def move(self, x, y, z, absolute=True):
        """ Move the given position. If absolute is true use a PR
        otherwise use PA. Most of the chinese machines don't handle
        negative values so absolute moves only works.
        
        """
        x, y = int(x*self.scale), int(y*self.scale)
        if absolute:
            if self.config.separate_z_moves:
                await self.write('PD;' if z else 'PU;')
                await self.write("PA%i,%i;" % (x, y))
            else:
                await self.write("%s%i,%i;" % ('PD' if z else 'PU', x, y))
        else:
            await self.write('PR%i,%i;' % (x, y))

    async def set_force(self, f):
        await self.write("FS%i;" % f)
        
    async def set_velocity(self, v):
        await self.write("VS%i;" % v)
        
    async def set_pen(self, p):
        await self.write("SP%i;" % p)
        
    async def finish(self):
        # Reinitialize
        await self.write("IN;")

