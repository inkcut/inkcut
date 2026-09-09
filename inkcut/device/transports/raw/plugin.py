"""
Copyright (c) 2019, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.
"""
import asyncio
import os
import sys
import traceback
from atom.atom import set_default
from atom.api import Atom, Value, ForwardInstance, Instance, Str, Enum
from inkcut.core.api import Plugin, Model, log
from inkcut.device.plugin import DeviceTransport, DeviceProtocol


class RawFdConfig(Model):
    device_path = Str("/dev/null").tag(config=True)
    mode = Enum('r+b', 'wb', 'r+', 'w').tag(config=True)


class RawFdProtocol(asyncio.Protocol, Atom):
    """Make a twisted protocol that delegates to the inkcut protocol
    implementation to have a consistent api (and use proper pep 8 formatting!).

    """
    _transport = ForwardInstance(lambda: RawFdTransport)
    delegate = Instance(DeviceProtocol)

    def connection_made(self, transport):
        self._transport = transport
        self._transport.connected = True
        self._transport.connection = self.transport

    def data_received(self, data):
        log.debug("<- {} | {}".format(self._transport.device_path, data))
        self._transport.last_read = data
        self.delegate.data_received(data)

    def connection_lost(self, reason):
        self._transport.connected = False
        self._transport.fd = None
        device_path = self._transport.device_path
        log.debug("-- {} | dropped: {}".format(device_path, reason))


class RawFdTransport(DeviceTransport):

    #: Default config
    config = Instance(RawFdConfig, ()).tag(config=True)

    #: The aiofile handle
    connection = Value()

    #: Current path
    device_path = Str()

    #: Wrapper
    _protocol = Instance(RawFdProtocol)

    async def connect(self):
        config = self.config
        device_path = self.device_path = config.device_path
        try:
            from aiofile import async_open
            self.connection = async_open(device_path, config.mode)
            log.debug("-- {} | opened".format(device_path))
            self._protocol = RawFdProtocol(delegate=self.protocol)
            self._protocol.connection_made(self.connection)
            if 'r' in config.mode:
                asyncio.create_task(self.start_reading())
            await self.protocol.init()
        except Exception as e:
            #: Make sure to log any issues as these tracebacks can get
            #: squashed by twisted
            log.error("{} | {}".format(device_path, traceback.format_exc()))
            raise

    async def start_reading(self):
        """ Read in loop """
        while (conn := self.connection):
            data = await conn.read()
            self._protocol.data_received(data)

    async def write(self, data):
        if not self.connection:
            raise IOError("{} is not opened".format(self.device_path))
        log.debug("-> {} | {}".format(self.device_path, data))
        if hasattr(data, 'encode'):
            data = data.encode()
        self.last_write = data
        await self.connection.write(data)

    async def disconnect(self):
        if self.connection:
            log.debug("-- {} | closed by request".format(self.device_path))
            self.connection.close()
            self.connection = None

    def __repr__(self):
        return self.device_path

