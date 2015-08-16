# -*- coding: utf-8 -*- 
'''
Created on Jan 16, 2015

@author: jrm
'''
from atom.api import Atom,Float,Instance,Unicode,Bool,Tuple,ContainerList,Int,Callable
from enaml.qt import QtCore
from enaml.core.declarative import Declarative,d_
from inkcut.workbench.core.svg import QtSvgDoc
from inkcut.workbench.core.area import AreaBase
from inkcut.workbench.core.utils import LoggingAtom


class IDeviceTransport(LoggingAtom):
    def connect(self,*args,**kwargs):
        pass
    
    def write(self,cmd):
        self.log.debug("transport.write(%s)"%cmd)
    
    def read(self):
        self.log.debug("transport.read()")
    
    def close(self):
        self.log.debug("transport.close()")
    
    def reset(self):
        self.close()
        self.connect()    

class IDeviceProtocol(LoggingAtom):
    transport = Instance(IDeviceTransport)
    
    def _default_transport(self):
        return IDeviceTransport()
    
    def init(self):
        self.log.debug("device.init()")
        pass
    
    def move(self,x,y,z):
        self.log.debug("device.move(%s,%s,%s)"%(x,y,z))
        pass
    
    def set_pen(self,p):
        self.log.debug("device.set_pen(%s)"%(p,))
        pass
    
    def set_velocity(self,v):
        self.log.debug("device.set_velocity(%s)"%(v,))
        pass
    
    def set_force(self,f):
        self.log.debug("device.set_force(%s)"%(f,))
        pass
    
    def write(self,cmd):
        self.transport.write(cmd)
        
    
class Device(AreaBase):
    name = Unicode('').tag(config=True)
    
    scale = ContainerList(Float(),default=[1,1]).tag(config=True)
    uses_roll = Bool(False).tag(config=True)

    position = ContainerList(Float(),default=[0.0,0.0,0.0])
    
    model = Instance(QtCore.QRectF)
    
    use_force = Bool(False).tag(config=True)
    use_speed = Bool(False).tag(config=True)
    force = Int(10).tag(config=True)
    speed = Int(20).tag(config=True)
    
    blade_offset = Float(QtSvgDoc.convertFromUnit(0.25, 'mm')).tag(config=True)
    overcut = Float(QtSvgDoc.convertFromUnit(2, 'mm')).tag(config=True)
    
    protocol = Instance(IDeviceProtocol)
    
    def _default_protocol(self):
        return IDeviceProtocol()
    
    def connect(self, *args, **kwargs):
        self.protocol.transport.connect(self, *args, **kwargs)
    
    def init(self):
        self.protocol.init()
    
    def move(self,x,y,z):
        self.position = [x,y,z]
        self.protocol.move(x,y,z)
        
    def set_velocity(self, v):
        self.protocol.set_velocity(v)
        
    def set_force(self, f):
        self.protocol.set_force(f)
    
    def set_pen(self, p):
        self.protocol.set_pen(p)
    
    def write(self,cmd):
        self.protocol.transport.write(cmd)
        
    def read(self):
        return self.protocol.transport.read()
        
    def close(self):
        self.protocol.transport.close() 


class DeviceDriver(Declarative):
    """ Provide meta info about this device """
    # ID of the device
    id = d_(Unicode())
    
    # Name of the device (optional)
    name = d_(Unicode())
    # Model of the device (optional)
    model = d_(Unicode())
    
    # Manufacturer of the device (optional)
    manufacturer = d_(Unicode())
    
    # Width of the device (required)
    width = d_(Unicode())
    
    # Length of the device, if it uses a roll, leave blank
    length = d_(Unicode())
    
    # Step resolution 
    resolution = d_(Unicode())
    
    # Factory to construct the device, 
    # takes a single argument for the protocol
    factory = d_(Callable())
    
    # IDs of the protocols supported by this device
    protocols = d_(ContainerList(Unicode()))
    
    # IDs of the transports supported by this device
    connections = d_(ContainerList(Unicode()))  


class DeviceProtocol(Declarative):
    # Id of the protocol
    id = d_(Unicode())
    
    # Name of the protocol (optional)
    name = d_(Unicode())
    
    # Factory to construct the protocol, 
    # takes a single argument for the transport
    factory = d_(Callable())
    
class DeviceTransport(Declarative):
    # Id of the transport
    id = d_(Unicode())
    
    # Name of the transport (optional)
    name = d_(Unicode())
    
    # Factory to construct the transport
    factory = d_(Callable())
    
    _transport = Instance(IDeviceTransport)
    
    settings = d_(Callable())
    
    _settings = Instance(Atom) 
    
    
