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
from inkcut.core.api import Plugin
from twisted.internet import reactor
from twisted.internet.serialport import SerialPort


class SerialPlugin(Plugin):
    """ Plugin for handling serial port communication
    
    """

    #: Available serial ports
    ports = List()

    #: Connection port
    connection = Instance(SerialPort)

    #: Serial port config
    port = Unicode()
    baudrate = Int(9600)
    bytesize = Enum(serial.EIGHTBITS, serial.SEVENBITS, serial.SIXBITS,
                    serial.FIVEBITS)
    parity = Enum(*serial.PARITY_NAMES.values())
    stopbits = Enum(serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE,
                    serial.STOPBITS_TWO)
    xonxoff = Bool()
    rtscts = Bool()

    # -------------------------------------------------------------------------
    # Defaults
    # -------------------------------------------------------------------------

    def _default_ports(self):
        return comports()

    def _default_parity(self):
        return serial.PARITY_NONE

    def _default_port(self):
        if self.ports:
            return self.ports[0].device

    # -------------------------------------------------------------------------
    # SerialPlugin API
    # -------------------------------------------------------------------------
    def refresh(self):
        self.ports = self._default_ports()

    def connect(self, protocol):
        self.connection = SerialPort(
            protocol,
            self.port,
            reactor,
            baudrate=self.baudrate,
            bytesize=self.bytesize,
            parity=serial.PARITY_NAMES[self.parity],
            stopbits=self.stopbits,
            xonxoff=self.xonxoff,
            rtscts=self.rtscts
        )

    def write(self, data):
        if not self.connection:
            raise IOError("Port is not opened")
        self.connection.write(data)

    def disconnect(self):
        if self.connection:
            self.connection.loseConnection()
            self.connection = None
