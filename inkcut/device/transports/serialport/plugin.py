# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import serial
import traceback
from atom.api import List, Instance, Enum, Bool, Int, Unicode
from inkcut.core.api import Plugin, Model, log
from inkcut.device.plugin import DeviceTransport
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, connectionDone
from twisted.internet.serialport import SerialPort
from serial.tools.list_ports import comports


#: Reverse key values
SERIAL_PARITIES = {v: k for k, v in serial.PARITY_NAMES.items()}


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
        return ""

    def refresh(self):
        self.ports = self._default_ports()


class InkcutProtocol(Protocol):
    """Make a twisted protocol that delegates to the inkcut protocol
    implementation to have a consistent api (and use proper pep 8 formatting!).
    
    """
    def __init__(self, parent, protocol):
        self.parent = parent
        self.delegate = protocol

    def connectionMade(self):
        self.parent.connected = True
        self.parent.connection = self.transport
        self.delegate.connection_made()

    def dataReceived(self, data):
        log.debug("<- {} | {}".format(self.parent.config.port, data))
        self.delegate.data_received(data)

    def connectionLost(self, reason=connectionDone):
        self.parent.connected = False
        self.delegate.connection_lost()


class SerialTransport(DeviceTransport):

    #: Default config
    config = Instance(SerialConfig, ())

    #: Connection port
    connection = Instance(SerialPort)

    #: Wrapper
    _protocol = Instance(InkcutProtocol)

    def connect(self):
        try:
            config = self.config

            #: Save a reference
            self.protocol.transport = self

            #: Make the wrapper
            self._protocol = InkcutProtocol(self, self.protocol)

            self.connection = SerialPort(
                self._protocol,
                config.port,
                reactor,
                baudrate=config.baudrate,
                bytesize=config.bytesize,
                parity=SERIAL_PARITIES[config.parity],
                stopbits=config.stopbits,
                xonxoff=config.xonxoff,
                rtscts=config.rtscts
            )
            log.debug("{} | opened".format(self.config.port))
        except Exception as e:
            #: Make sure to log any issues as these tracebacks can get
            #: squashed by twisted
            log.error("{} | {}".format(
                self.config.port, traceback.format_exc()
            ))
            raise

    def write(self, data):
        if not self.connection:
            raise IOError("Port is not opened")
        log.debug("-> {} | {}".format(self.config.port, data))
        self._protocol.transport.write(data)

    def disconnect(self):
        if self.connection:
            log.debug("{} | closed".format(self.config.port))
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

