# -*- coding: utf-8 -*-
'''
Created on Jul 25, 2015

@author: jrm
'''
import serial
from serial.tools import list_ports
from atom.api import Instance, Unicode, Int, List
from inkcut.workbench.core.device import IDeviceTransport
from inkcut.workbench.core.utils import ConfigurableAtom

class SerialPortSettings(ConfigurableAtom):
    ports = List(Unicode())
    port = Unicode()
    baudrate = Int(9600)
    
    def _default_ports(self):
        return [it[0] for it in list_ports()]
    
    def _default_port(self):
        return self.ports[0]
        

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