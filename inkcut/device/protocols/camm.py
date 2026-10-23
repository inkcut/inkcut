# -*- coding: utf-8 -*-
"""
Created on Dec 30, 2016

@author: jrm
"""
from inkcut.device.plugin import DeviceProtocol


class CAMMGL1Protocol(DeviceProtocol):
    async def init(self):
        await self.write("IN;")
    
    async def move(self, x, y, z, absolute=True):
        await self.write("{z}{x},{y};".format(x=x, y=y, z=z and "D" or "M", ))
        
    async def set_force(self, f):
        await self.write("FS{f};".format(f=f))
        
    async def set_velocity(self, v):
        await self.write("VS{v};".format(v=v))
        
    async def set_pen(self, p):
        await self.write("SP{p};".format(p=p))
