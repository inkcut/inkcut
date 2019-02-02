# -*- coding: utf-8 -*-
"""
Copyright (c) 2019, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Feb 2, 2019

@author: jrm
"""
import os
import sys
import traceback
from atom.atom import set_default
from atom.api import Value, Instance, Unicode, Enum
from inkcut.core.api import Plugin, Model, log
from inkcut.device.plugin import DeviceTransport
from twisted.internet import reactor, stdio
from twisted.internet.protocol import Protocol, connectionDone


class RawFdConfig(Model):
    device_path = Unicode("/dev/null").tag(config=True)
    mode = Enum('r+b', 'wb', 'r+', 'w').tag(config=True)


class RawFdProtocol(Protocol):
    """Make a twisted protocol that delegates to the inkcut protocol
    implementation to have a consistent api (and use proper pep 8 formatting!).

    """
    def __init__(self, transport, protocol):
        self._transport = transport
        self.delegate = protocol

    def connectionMade(self):
        self._transport.connected = True
        self._transport.connection = self.transport
        self.delegate.connection_made()

    def dataReceived(self, data):
        log.debug("<- {} | {}".format(self._transport.device_path, data))
        self._transport.last_read = data
        self.delegate.data_received(data)

    def connectionLost(self, reason=connectionDone):
        self._transport.connected = False
        self._transport.fd = None
        device_path = self._transport.device_path
        log.debug("-- {} | dropped: {}".format(device_path, reason))
        self.delegate.connection_lost()


class RawFdTransport(DeviceTransport):

    #: Default config
    config = Instance(RawFdConfig, ()).tag(config=True)

    #: The device handles
    fd = Value()

    #: Current path
    device_path = Unicode()

    #: Wrapper
    _protocol = Instance(RawFdProtocol)

    #: A raw device connection
    connection = Instance(stdio.StandardIO)

    def connect(self):
        config = self.config
        device_path = self.device_path = config.device_path
        if 'win32' in sys.platform:
            # Well, technically it works, but only with stdin and stdout
            raise OSError("Raw device support cannot be used on Windows")

        try:
            self.fd = open(device_path, config.mode)
            fd = self.fd.fileno()
            log.debug("-- {} | opened".format(device_path))
            self._protocol = RawFdProtocol(self, self.protocol)
            self.connection = stdio.StandardIO(self._protocol, fd, fd)
        except Exception as e:
            #: Make sure to log any issues as these tracebacks can get
            #: squashed by twisted
            log.error("{} | {}".format(device_path, traceback.format_exc()))
            raise

    def write(self, data):
        if not self.connection:
            raise IOError("{} is not opened".format(self.device_path))
        log.debug("-> {} | {}".format(self.device_path, data))
        if hasattr(data, 'encode'):
            data = data.encode()
        self.last_write = data
        self.connection.write(data)

    def disconnect(self):
        if self.connection:
            log.debug("-- {} | closed by request".format(self.device_path))
            self.connection.loseConnection()
            self.connection = None

    def __repr__(self):
        return self.device_path

