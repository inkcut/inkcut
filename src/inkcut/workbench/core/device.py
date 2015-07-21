# -*- coding: utf-8 -*- 
'''
Created on Jan 16, 2015

@author: jrm
'''
from atom.api import Float,Instance,Unicode,Bool,ContainerList,Int
import serial
from inkcut.workbench.core.utils import ConfigurableAtom, LoggingAtom
from enaml.qt import QtCore
from inkcut.workbench.core.svg import QtSvgDoc
from inkcut.workbench.core.area import AreaBase

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
    
    position = ContainerList(Float(),default=[0.0,0.0,0.0]).tag(config=True)
    
    model = Instance(QtCore.QRectF)
    
    use_force = Bool(False).tag(config=True)
    use_speed = Bool(False).tag(config=True)
    force = Int(10).tag(config=True)
    speed = Int(20).tag(config=True)
    
    blade_offset = Float(QtSvgDoc.convertFromUnit(0.25, 'mm'))
    overcut = Float(QtSvgDoc.convertFromUnit(2, 'mm'))
    
    transport_def = Unicode('vycut.core.device.DebugTransport')
    transport = Instance(IDeviceTransport)
    protocol_def = Unicode('vycut.core.device.HPGLProtocol')
    protocol = Instance(IDeviceProtocol)
    
    def _default_protocol(self):
        return IDeviceProtocol()
    
    def _default_transport(self):
        return IDeviceTransport()
    
    def connect(self, *args, **kwargs):
        self.transport.connect(self, *args, **kwargs)
    
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
        self.transport.write(cmd)
        
    def read(self):
        return self.transport.read()
        
    def close(self):
        self.transport.close() 


class HPGLProtocol(IDeviceProtocol):
    def init(self):
        self.write("IN;")
    
    def move(self,x,y,z):
        self.write("%s%i,%i;"%(z and "PD" or "PU",x,y))
        
    def set_force(self, f):
        self.write("FS%i;"%f)
        
    def set_velocity(self, v):
        self.write("VS%i;"%v)
        
    def set_pen(self, p):
        self.write("SP%i;"%p)
        
class DMPLProtocol(IDeviceProtocol):
    def init(self):
        self.write(" ;:H A L0 ")
    
    def move(self,x,y,z):
        self.write("%s%i,%i "%(z and "D" or "U",x,y))
        
    def set_pen(self, p):
        self.write("EC%i "%p)
        
    def set_velocity(self, v):
        self.write("V%i "%v)
        
    def set_force(self, f):
        self.write("BP%i "%f)

class GPGLProtocol(IDeviceProtocol):
    def init(self):
        self.write("H")
        
    def move(self,x,y,z):
        self.write("%s%i,%i;"%(z and "M" or "D",x,y))
        
    def set_velocity(self, v):
        self.write("!%i"%v)
        
    def set_force(self, f):
        self.write("*%i"%f)
    


class DebugTransport(IDeviceTransport):
    pass

class SerialTransport(IDeviceTransport):
    port = Instance(serial.Serial)
    
    def init(self):
        self.connect()
    
    def connect(self, *args, **kwargs):
        self.port = serial.Serial(*args, **kwargs)
    
    def read(self):
        return self.port.read()
    
    def write(self,cmd):
        self.port.write(cmd)
        
    def close(self):
        self.port.close()
        

class PrinterTransport(IDeviceTransport):
    """ TODO: Implement for windows """
    printer = None
    
    def connect(self, *args, **kwargs):
        self.printer = None
    
    def write(self,cmd):
        pass
    
