# -*- coding: utf-8 -*-
"""
Copyright (c) 2017-2019, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import serial
import traceback
from atom.atom import set_default
from atom.api import List, Instance, Enum, Bool, Int, Str
from inkcut.core.api import Plugin, Model, log
from inkcut.device.plugin import DeviceTransport
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, connectionDone
from twisted.internet.serialport import SerialPort
from serial.tools.list_ports import comports

from inkcut.device.transports.raw.plugin import RawFdTransport, RawFdProtocol


#: Reverse key values
SERIAL_PARITIES = {v: k for k, v in serial.PARITY_NAMES.items()}


def patch_pyserial_if_needed():
    """ A workaround for
    https://github.com/pyserial/pyserial/issues/286
    """
    try:
        from serial.tools.list_ports_common import ListPortInfo
    except ImportError:
        return
    try:
        dummy = ListPortInfo()
        dummy == None
        log.debug("pyserial patch not needed")
    except AttributeError:
        def __eq__(self, other):
            return isinstance(other, ListPortInfo) \
                and self.device == other.device
        ListPortInfo.__eq__ = __eq__
        log.debug("pyserial patched")
patch_pyserial_if_needed()


class SerialConfig(Model):
    #: Available serial ports
    ports = List()

    #: Serial port config
    port = Str().tag(config=True)
    baudrate = Int(9600).tag(config=True)
    bytesize = Enum(serial.EIGHTBITS, serial.SEVENBITS, serial.SIXBITS,
                    serial.FIVEBITS).tag(config=True)
    parity = Enum(*serial.PARITY_NAMES.values()).tag(config=True)
    stopbits = Enum(serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE,
                    serial.STOPBITS_TWO).tag(config=True)
    xonxoff = Bool().tag(config=True)
    rtscts = Bool().tag(config=True)
    dsrdtr = Bool().tag(config=True)

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


class SerialTransport(RawFdTransport):

    #: Default config
    config = Instance(SerialConfig, ()).tag(config=True)

    #: Connection port
    connection = Instance(SerialPort)

    #: Whether a serial connection spools depends on the device (configuration)
    always_spools = set_default(False)

    def connect(self):
        config = self.config
        self.device_path = config.port
        try:
            #: Save a reference
            self.protocol.transport = self

            #: Make the wrapper
            self._protocol = RawFdProtocol(self, self.protocol)

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

            # Twisted is missing this
            if config.dsrdtr:
                try:
                    self.connection._serial.dsrdtr = True
                except AttributeError as e:
                    log.warning("{} | dsrdtr is not supported {}".format(
                        config.port, e))

            log.debug("{} | opened".format(config.port))
        except Exception as e:
            #: Make sure to log any issues as these tracebacks can get
            #: squashed by twisted
            log.error("{} | {}".format(config.port, traceback.format_exc()))
            raise


class SerialPlugin(Plugin):
    """ Plugin for handling serial port communication

    """

    # -------------------------------------------------------------------------
    # SerialPlugin API
    # -------------------------------------------------------------------------
