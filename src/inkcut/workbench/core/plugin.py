# -*- coding: utf-8 -*-
'''
Created on Aug 2, 2015

@author: jrm
'''
from atom.api import Instance, List, Unicode
from inkcut.workbench.core.utils import SingletonPlugin
from inkcut.workbench.core.media import Media
from inkcut.workbench.core.device import Device, DeviceTransport, DeviceProtocol,\
    DeviceDriver


DEVICES_POINT = 'inkcut.workbench.core.devices'
        
PROTOCOLS_POINT = 'inkcut.workbench.core.protocols'
        
TRANSPORTS_POINT = 'inkcut.workbench.core.transports'

MEDIA_POINT = 'inkcut.workbench.core.media'

class InkcutCorePlugin(SingletonPlugin):
    """ Plugin loads all other plugins except the UI 
    and determines the default device and media.
    """
    
    
    # Available classes
    _protocols = List()
    _transports = List()
    _devices = List()
    _media = List()
    
    # Active
    device = Instance(Device)
    device_id = Unicode().tag(config=True)
    
    media = Instance(Media)
    media_id = Unicode().tag(config=True)
    
    
    def start(self):
        self.workbench.register_plugins('inkcut/plugins')
        self._refresh_transports()
        self._refresh_protocols()
        self._refresh_devices()
        self._refresh_media()
    
    def _refresh_transports(self):
        workbench = self.workbench
        point = workbench.get_extension_point(TRANSPORTS_POINT)
        extensions = sorted(point.extensions, key=lambda ext: ext.rank)

        transports = []
        for extension in extensions:
            transports.extend(extension.get_children(DeviceTransport))
        
        self._transports = transports
        return transports
    
    def _refresh_protocols(self):
        workbench = self.workbench
        point = workbench.get_extension_point(PROTOCOLS_POINT)
        extensions = sorted(point.extensions, key=lambda ext: ext.rank)

        protocols = []
        for extension in extensions:
            protocols.extend(extension.get_children(DeviceProtocol))
        
        self._protocols = protocols
        return protocols
    
    def _refresh_devices(self):
        workbench = self.workbench
        point = workbench.get_extension_point(DEVICES_POINT)
        extensions = sorted(point.extensions, key=lambda ext: ext.rank)

        devices = []
        for extension in extensions:
            devices.extend(extension.get_children(DeviceDriver))
        
        self._devices = devices
        return devices
    
    def _refresh_media(self):
        workbench = self.workbench
        point = workbench.get_extension_point(MEDIA_POINT)
        extensions = sorted(point.extensions, key=lambda ext: ext.rank)

        media = []
        for extension in extensions:
            media.extend(extension.get_children(DeviceDriver))
        
        self._media = media
        return media
    
    def _default_device(self):
        return Device()
    
    def _default_media(self):
        return Media()
    