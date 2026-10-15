# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

Thanks to Lex Wernars

@author: jrm
@author: lwernars
"""
from inkcut.device.plugin import DeviceProtocol


class GPGLProtocol(DeviceProtocol):
    async def init(self):
        await self.write("H")

    async def move(self, x, y, z, absolute=True):
        await self.write("%s%i,%i"%('D' if z else 'M', x, y))

    async def set_velocity(self, v):
        await self.write('!%i' % v)

    async def set_force(self, f):
        await self.write("FX%i,1" % f)

    async def set_pen(self, p):
        pass
