"""
Copyright (c) 2017-2019, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.
"""
import asyncio
import serial
import traceback
from atom.atom import set_default
from atom.api import Atom, List, ForwardInstance, Instance, Enum, Bool, Int, Str
from inkcut.core.api import Plugin, Model, log
from inkcut.device.plugin import DeviceTransport, DeviceProtocol
from serial.tools.list_ports import comports
from .serial import create_serial_connection, SerialTransport as SerialConnection


#: Reverse key values
SERIAL_PARITIES = {v: k for k, v in serial.PARITY_NAMES.items()}


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

class SerialProtocol(asyncio.Protocol, Atom):
    """Make a twisted protocol that delegates to the inkcut protocol
    implementation to have a consistent api (and use proper pep 8 formatting!).

    """
    _transport = ForwardInstance(lambda: SerialTransport)
    delegate = Instance(DeviceProtocol)

    def connection_made(self, transport: SerialConnection):
        self._transport.connected = True

    def data_received(self, data):
        log.debug("<- {} | {}".format(self._transport.device_path, data))
        self._transport.last_read = data
        self.delegate.data_received(data)

    def connection_lost(self, reason):
        self._transport.connected = False
        device_path = self._transport.device_path
        log.debug("-- {} | dropped: {}".format(device_path, reason))


class SerialTransport(DeviceTransport):

    #: Default config
    config = Instance(SerialConfig, ()).tag(config=True)

    #: Connection port
    connection = Instance(SerialConnection)

    #: Used to wait until write is actually sent
    pending_write = Instance(asyncio.Future)

    #: The original port name
    device_path = Str()

    #: Whether a serial connection spools depends on the device (configuration)
    always_spools = set_default(False)

    async def connect(self):
        config = self.config
        self.device_path = config.port
        try:
            #: Save a reference
            self.protocol.transport = self

            #: Make the wrapper
            self.connection, serial_protocol = await create_serial_connection(
                loop=asyncio.get_running_loop(),
                protocol_factory=lambda: SerialProtocol(_transport=self, delegate=self.protocol),
                url=config.port,
                baudrate=config.baudrate,
                bytesize=config.bytesize,
                parity=SERIAL_PARITIES[config.parity],
                stopbits=config.stopbits,
                xonxoff=config.xonxoff,
                rtscts=config.rtscts
            )

            # This is a patched in in serial.py
            self.connection._wrote_callback = self.on_write_complete

            # Twisted is missing this
            if config.dsrdtr:
                try:
                    self.connection._serial.dsrdtr = True
                except AttributeError as e:
                    log.warning("{} | dsrdtr is not supported {}".format(
                        config.port, e))

            await self.connected_event.wait()
            log.debug("{} | opened".format(config.port))
            await self.protocol.init()
        except Exception as e:
            #: Make sure to log any issues as these tracebacks can get
            #: squashed by twisted
            log.error("{} | {}".format(config.port, traceback.format_exc()))
            raise

    def on_write_complete(self, data: bytes):
        # This is invoked in SerialTransport._write_data
        future = self.pending_write
        if future and not future.done():
            if not data:
                future.set_result(False)  # failed
            elif self.connection.get_write_buffer_size() == 0:
                future.set_result(True)  # complete
            # else not done

    async def write(self, data):
        log.debug("-> {} | {}".format(self.device_path, data))
        if pending := self.pending_write:
            await pending # Wait until previous completes
        try:
            loop = asyncio.get_event_loop()
            self.pending_write = loop.create_future()
            # Write just puts it into the write buffer
            # So wait until the buffer is empty (all written)
            # or the connection drops
            if hasattr(data, 'encode'):
                data = data.encode()
            self.connection.write(data)
            await self.pending_write
            return
        finally:
            self.pending_write = None

    async def disconnect(self):
        if pending := self.pending_write:
            pending.cancel()
            self.pending_write = None
        if self.connection:
            self.connection.close()


class SerialPlugin(Plugin):
    """ Plugin for handling serial port communication

    """

    # -------------------------------------------------------------------------
    # SerialPlugin API
    # -------------------------------------------------------------------------
