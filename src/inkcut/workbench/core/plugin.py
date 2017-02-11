# -*- coding: utf-8 -*-
'''
Created on Aug 2, 2015

@author: jrm
'''
from atom.api import Instance, List, Unicode, observe
from inkcut.workbench.core.utils import SingletonPlugin
from inkcut.workbench.core.media import Media
from inkcut.workbench.core.device import Device, DeviceProtocol,DeviceDriver
import traceback


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
    protocol_id = Unicode().tag(config=True)
    connection_id = Unicode().tag(config=True)
    
    media = Instance(Media)
    media_id = Unicode().tag(config=True)
    
    
    def start(self):
        self.workbench.register_plugins('inkcut/plugins')
        #self._refresh_transports()
        self._refresh_protocols()
        self._refresh_devices()
        self._refresh_media()
    
#     def _refresh_transports(self):
#         workbench = self.workbench
#         point = workbench.get_extension_point(TRANSPORTS_POINT)
#         extensions = sorted(point.extensions, key=lambda ext: ext.rank)
# 
#         transports = []
#         for extension in extensions:
#             transports.extend(extension.get_children(DeviceTransport))
#         
#         self._transports = transports
#         return transports
    
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
            for driver in extension.get_children(DeviceDriver):
                try:
                    if not driver.id:
                        driver.id = "{} {}".format(driver.manufacturer,driver.model)
                    devices.append(driver)
                except:
                    self.log.error(traceback.format_exc())
                
        
        self._devices = devices
        return devices
    
    @property
    def available_devices(self):
        return self._devices
    
    def _refresh_media(self):
        workbench = self.workbench
        point = workbench.get_extension_point(MEDIA_POINT)
        extensions = sorted(point.extensions, key=lambda ext: ext.rank)

        media = []
        for extension in extensions:
            media.extend(extension.get_children(DeviceDriver))
        
        self._media = media
        return media
    
    def get_protocol_by_id(self,id):
        for proto in self._protocols:
            if proto.id == id:
                return proto
        raise KeyError("{} is not a registered protocol.".format(id))
    
    def get_driver_by_id(self,id):
        for dev in self._devices:
            if dev.id == id:
                return dev
        raise KeyError("{} is not a registered device.".format(id))
    
    #@observe('device_id','protocol_id')
    def _default_device(self):
        """ Return the default device as configured """
        try:
            dvr = self.get_driver_by_id(self.device_id)
        except KeyError:
            dvr = self.get_driver_by_id('Inkcut Virtual device') 
        
        self.log.debug("Loading {}".format(dvr.id))
        proto = self.get_protocol_by_id(dvr.protocols[0])
        driver = dvr.factory(dvr,proto.factory())
        return Device(driver=driver)
    
    def _default_media(self):
        return Media()
    