# -*- coding: utf-8 -*-
"""
Copyright (c) 2020, Laszlo Ducsai

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Oct 26, 2020

@author: ducsi
"""
import sys
import traceback
from atom.atom import set_default
from atom.api import List, Instance, Enum, Bool, Int, Str
from inkcut.core.api import Plugin, Model, log
from inkcut.device.plugin import DeviceTransport
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtSerialPort import QSerialPortInfo



class IdNameItem:  
    def __init__(self, id, name):  
        self.id :int = id  
        self.name = name 


class QtSerialConfig(Model):
    device_path = Str()
    
    #: Available serial ports
    ports = List()
    #: Serial port config
    port = Str().tag(config=True)

    flowcontrols = []
    # Available FlowControls
    flowcontrols.append( IdNameItem(QSerialPort.NoFlowControl, 'No flow control') ) 
    flowcontrols.append( IdNameItem(QSerialPort.HardwareControl,'Hardware flow control (RTS/CTS)') ) 
    flowcontrols.append( IdNameItem(QSerialPort.SoftwareControl,'Software flow control (XON/XOFF)') ) 
    flowcontrols.append( IdNameItem(QSerialPort.UnknownFlowControl,'Unknown flow control (obsolete value)') ) 
    #: FlowControl config
    flowcontrol=Int(0).tag(config=True)
    
    #: Available BaudRates
    baudrates = Enum(110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 256000)
    #: BaudRate config
    baudrate = Int(9600).tag(config=True)
    
    parities = []
    # Available Parities
    parities.append( IdNameItem(QSerialPort.NoParity, 'No Parity') ) 
    parities.append( IdNameItem(QSerialPort.EvenParity, 'Even') ) 
    parities.append( IdNameItem(QSerialPort.OddParity, 'Odd') ) 
    parities.append( IdNameItem(QSerialPort.SpaceParity, 'Space') ) 
    parities.append( IdNameItem(QSerialPort.MarkParity, 'Mark') ) 
    parities.append( IdNameItem(QSerialPort.UnknownParity, 'Unknown') ) 
    #: Parity config
    parity=Int(0).tag(config=True)    

    list_stopbits = []
    # Available Stopbits
    list_stopbits.append( IdNameItem(QSerialPort.OneStop, '1 stop bit') ) 
    list_stopbits.append( IdNameItem(QSerialPort.OneAndHalfStop, '1.5 stop bits (Windows only)') ) 
    list_stopbits.append( IdNameItem(QSerialPort.TwoStop, '2 stop bits') ) 
    #: Stopbits config
    stopbits=Int(1).tag(config=True) 
    
    bytesize = Enum(8, 7, 6, 5).tag(config=True) 
    

    # -------------------------------------------------------------------------
    # Defaults
    # -------------------------------------------------------------------------
    def _default_ports(self):
        return self.get_serial_ports()
    
    def _default_port(self):
        if self.ports:
            return self.ports[0].portName()
        return ""    

    def refresh(self):
        self.ports = self._default_ports()
        
    def get_serial_ports(self):
        info_list = QSerialPortInfo()
        serial_list = info_list.availablePorts()
        return serial_list    
        

class QtSerialTransport(DeviceTransport):

    #: Default config
    config = Instance(QtSerialConfig, ()).tag(config=True)
    #: Current path
    device_path = Str()
    #: Connection port
    connection = Instance(QSerialPort)

    #: Whether a serial connection spools depends on the device (configuration)
    always_spools = set_default(False)
    
    def open_serial_port(self, config):
        try:
            serial_port = QSerialPort()
            serial_port.setPortName(config.port)
            #Setting the AllDirections flag is supported on all platforms. Windows supports only this mode.
            serial_port.setBaudRate(config.baudrate, QSerialPort.AllDirections)
            serial_port.setParity(config.parity)
            serial_port.setStopBits(config.stopbits)
            serial_port.setDataBits(config.bytesize)
            serial_port.setFlowControl(config.flowcontrol)
            serial_port.open(QSerialPort.ReadWrite)
            return serial_port
        except Exception as e:
            log.error("{}".format(traceback.format_exc()))
            return None    

    def connect(self):
        config = self.config
        #self.device_path = config.port
        device_path = self.device_path = config.port
        try:
            #: Save a reference
            self.protocol.transport = self
            
            self.connection = self.open_serial_port(config)
            self.connected = True
            log.debug("{} | opened".format(config.port))
            self.protocol.connection_made()
            
        except Exception as e:
            #: Make sure to log any issues
            log.error("{} | {}".format(config.port, traceback.format_exc()))
            raise
            
    def write(self, data):
        if not self.connection:
            raise IOError("{} is not opened".format(self.device_path))
        log.debug("-> {} | {}".format(self.device_path, data))
        if hasattr(data, 'encode'):
            data = data.encode()
        self.last_write = data
        self.connection.write(data)
        self.connection.waitForBytesWritten(-1)
    def disconnect(self):
        if self.connection:
            self.connection.waitForBytesWritten(-1)
            log.debug("-- {} | closed by request".format(self.device_path))
            self.connected=False
            self.connection.close()
            self.connection = None

    def __repr__(self):
        return self.device_path


class QtSerialPlugin(Plugin):
    """ Plugin for handling serial port communication

    """
    # -------------------------------------------------------------------------
    # SerialPlugin API
    # -------------------------------------------------------------------------