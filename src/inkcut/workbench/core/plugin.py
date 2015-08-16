# -*- coding: utf-8 -*-
'''
Created on Aug 2, 2015

@author: jrm
'''
from atom.api import Instance
from inkcut.workbench.core.utils import SingletonPlugin
from inkcut.workbench.core.media import Media
from inkcut.workbench.core.device import Device


class InkcutCorePlugin(SingletonPlugin):
    
    device = Instance(Device)
    media = Instance(Media)
    
    def start(self):
        self._refresh_transports()
        self._refresh_protocols()
        self._refresh_devices()
    
    def _refresh_transports(self):
        pass
    
    
    def _refresh_protocols(self):
        pass
    
    
    def _refresh_devices(self):
        pass
    
    def _default_device(self):
        return Device()
    
    def _default_media(self):
        return Media()
    