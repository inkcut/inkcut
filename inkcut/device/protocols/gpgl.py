# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

Thanks to Lex Wernars

@author: jrm
@author: lwernars
"""
from atom.api import Bool, Instance
from inkcut.core.api import Model
from inkcut.device.plugin import DeviceProtocol


class GPGLConfig(Model):
    #: Terminate each command with ETX (0x03). Machines like the Cameo 4
    #: do not run a command until it is terminated.
    append_etx = Bool().tag(config=True)


class GPGLProtocol(DeviceProtocol):
    config = Instance(GPGLConfig, ()).tag(config=True)

    async def write(self, data):
        if self.config.append_etx:
            data += "\x03"
        await super().write(data)

    async def init(self):
        await self.write("\x03\x03H")

    async def move(self, x, y, z, absolute=True):
        await self.write("\x03%s%i,%i"%('D' if z else 'M', x, y))

    async def set_velocity(self, v):
        await self.write('\x03!%i' % v)

    async def set_force(self, f):
        await self.write("\x03FX%i,1" % f)

    async def set_pen(self, p):
        pass
