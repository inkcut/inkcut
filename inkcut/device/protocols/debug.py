# -*- coding: utf-8 -*-
'''
Created on Oct 23, 2015

@author: jrm
'''
import asyncio
from inkcut.device.plugin import DeviceProtocol
from inkcut.core.utils import log


class DebugProtocol(DeviceProtocol):
    """ A protocol that just logs what is called """
    async def init(self):
        log.debug("protocol.connectionMade()")
    
    async def move(self, x, y, z, absolute=True):
        log.debug("protocol.move({x},{y},{z})".format(x=x, y=y, z=z))
        #: Wait some time before we get there
        await asyncio.sleep(0.1)
        
    async def set_pen(self, p):
        log.debug("protocol.set_pen({p})".format(p=p))
        
    async def set_velocity(self, v):
        log.debug("protocol.set_velocity({v})".format(v=v))
        
    async def set_force(self, f):
        log.debug("protocol.set_force({f})".format(f=f))

    def data_received(self, data):
        log.debug("protocol.data_received({}".format(data))
