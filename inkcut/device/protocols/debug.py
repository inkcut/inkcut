# -*- coding: utf-8 -*-
'''
Created on Oct 23, 2015

@author: jrm
'''
from inkcut.device.plugin import DeviceProtocol
from inkcut.core.utils import async_sleep, log


class DebugProtocol(DeviceProtocol):
    """ A protocol that just logs what is called """
    def connection_made(self):
        log.debug("protocol.connectionMade()")
    
    def move(self, x, y, z, absolute=True):
        log.debug("protocol.move({x},{y},{z})".format(x=x, y=y, z=z))
        #: Wait some time before we get there
        return async_sleep(0.1)
        
    def set_pen(self, p):
        log.debug("protocol.set_pen({p})".format(p=p))
        
    def set_velocity(self, v):
        log.debug("protocol.set_velocity({v})".format(v=v))
        
    def set_force(self, f):
        log.debug("protocol.set_force({f})".format(f=f))

    def data_received(self, data):
        log.debug("protocol.data_received({}".format(data))

    def connection_lost(self):
        log.debug("protocol.connection_lost()")