# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import serial
from serial.tools.list_ports import comports
from atom.api import List, Instance, Enum, Bool, Int, Unicode
from inkcut.core.api import Plugin, Model
from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from inkcut.device.plugin import DeviceTransport


class SerialConfig(Model):
    #: Available serial ports
    ports = List()

    #: Serial port config
    port = Unicode().tag(config=True)
    baudrate = Int(9600).tag(config=True)
    bytesize = Enum(serial.EIGHTBITS, serial.SEVENBITS, serial.SIXBITS,
                    serial.FIVEBITS).tag(config=True)
    parity = Enum(*serial.PARITY_NAMES.values()).tag(config=True)
    stopbits = Enum(serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE,
                    serial.STOPBITS_TWO).tag(config=True)
    xonxoff = Bool().tag(config=True)
    rtscts = Bool().tag(config=True)

    # -------------------------------------------------------------------------
    # Defaults
    # -------------------------------------------------------------------------

    def _default_ports(self):
        return comports()

    def _default_parity(self):
        return 'None'

    def _default_port(self):
        if self.ports:
            return self.ports[0].device

    def refresh(self):
        self.ports = self._default_ports()


class SerialTransport(DeviceTransport):

    #: Default config
    config = Instance(SerialConfig, ())

    #: Connection port
    connection = Instance(SerialPort)

    def connect(self, protocol):
        config = self.config
        self.connection = SerialPort(
            protocol,
            config.port,
            reactor,
            baudrate=config.baudrate,
            bytesize=config.bytesize,
            parity=serial.PARITY_NAMES[config.parity],
            stopbits=config.stopbits,
            xonxoff=config.xonxoff,
            rtscts=config.rtscts
        )

    def write(self, data):
        if not self.connection:
            raise IOError("Port is not opened")
        self.connection.write(data)

    def disconnect(self):
        if self.connection:
            self.connection.loseConnection()
            self.connection = None

    def __repr__(self):
        return self.config.port

class SerialPlugin(Plugin):
    """ Plugin for handling serial port communication
    
    """

    # -------------------------------------------------------------------------
    # SerialPlugin API
    # -------------------------------------------------------------------------

