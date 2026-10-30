"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 19, 2017
"""
import asyncio
import sys
import traceback


from atom.atom import set_default
from atom.api import Atom, List, ForwardInstance, Instance, Str
from inkcut.core.api import Plugin, Model, log
from inkcut.device.plugin import DeviceTransport, DeviceProtocol

try:
    if sys.platform == 'win32':
        import win32print
    else:
        import cups
    PRINTER_AVAILABLE = True
except ImportError as e:
    log.error(e)
    PRINTER_AVAILABLE = False

# -----------------------------------------------------------------------------
# Abstract API
# -----------------------------------------------------------------------------
class PrinterConfig(Model):
    #: Available printers
    printers = List()

    #: Serial port config
    printer = Str().tag(config=True)

    # -------------------------------------------------------------------------
    # Defaults
    # -------------------------------------------------------------------------
    def _default_printers(self):
        raise NotImplementedError

    def _default_printer(self):
        if self.printers:
            return self.printers[0]
        return ""

    def refresh(self):
        self.printers = self._default_printers()


class PrinterConnection(Model):

    #: Reference to the transport interface
    transport = Instance(DeviceTransport)

    #: The actual printer
    printer = Instance(object)

    async def open(self):
        raise NotImplementedError

    async def write(self, data):
        log.debug("-> {} | {}".format(self.transport.config.printer, data))

    async def close(self):
        raise NotImplementedError


# -----------------------------------------------------------------------------
# Windows API
# -----------------------------------------------------------------------------
class Win32PrinterConfig(PrinterConfig):

    def _default_printers(self):
        if not PRINTER_AVAILABLE:
            return []
        try:
            return [p[2] for p in win32print.EnumPrinters(
                    win32print.PRINTER_ENUM_LOCAL)]
        except Exception as e:
            if 'RPC server is unavailable' in str(e):
                return []  # Ignore this error
            raise


class Win32PrinterConnection(PrinterConnection):
    job = Instance(object)

    async def open(self):
        p = win32print.OpenPrinter(self.transport.config.printer)
        self.job = win32print.StartDocPrinter(
            p, 1, ("Inkcut job", None, "RAW"))
        win32print.StartPagePrinter(p)
        self.printer = p

        #: Sync
        self.transport.connected = True
        await self.transport.protocol.init()

    async def write(self, data):
        super(Win32PrinterConnection, self).write(data)
        win32print.WritePrinter(self.printer, bytearray(data,'ascii'))

    async def close(self):
        p = self.printer
        win32print.EndPagePrinter(p)
        win32print.EndDocPrinter(p)
        win32print.ClosePrinter(p)
        #: Sync
        self.transport.connected = False

# -----------------------------------------------------------------------------
# Cups API
# -----------------------------------------------------------------------------
class CupsPrinterConfig(PrinterConfig):

    def _default_printers(self):
        if not PRINTER_AVAILABLE:
            return []
        try:
            return list(sorted(cups.Connection().getPrinters().keys()))
        except Exception as e:
            log.warning("Failed to get printer list: {}".format(e))
            return []


# -----------------------------------------------------------------------------
# LPR API
# -----------------------------------------------------------------------------
class LPRProtocol(asyncio.SubprocessProtocol, Atom):
    parent = ForwardInstance(lambda: PrinterTransport)
    delegate = Instance(DeviceProtocol)

    def connection_made(self, transport):
        self.parent.connected = True

    def pipe_data_received(self, fd, data):
        if fd == 2:
            log.error("LPR error: {}".format(data))
        else:
            self.delegate.data_received(data)

    def process_exited(self):
        self.parent.connected = False


class LPRPrinterConnection(PrinterConnection):
    #: Delegate
    _protocol = Instance(LPRProtocol)

    async def open(self):
        t = self.transport
        loop = asyncio.get_running_loop()
        self._protocol = LPRProtocol(parent=t, delegate=t.protocol)
        self.printer, _ = await loop.subprocess_exec(
            lambda: self._protocol,
            'lpr', '-P', t.config.printer, '-o', 'raw')

    async def write(self, data):
        await super().write(data)
        if hasattr(data, 'encode'):
            data = data.encode()
        self.printer.get_pipe_transport(0).write(data)

    async def close(self):
        #: EOF on stdin makes lpr submit the job; wait for it instead of
        #: killing it, otherwise the job is discarded
        self.printer.get_pipe_transport(0).close()
        while self.printer.get_returncode() is None:
            await asyncio.sleep(0.1)
        rc = self.printer.get_returncode()
        if rc:
            log.error("LPR exited with {}".format(rc))
        self.printer.close()


# -----------------------------------------------------------------------------
# Inkcut API
# -----------------------------------------------------------------------------
class PrinterTransport(DeviceTransport):

    #: Default config
    config = Instance(PrinterConfig).tag(config=True)

    #: Delegate to the implementation based on the current platform
    connection = Instance(PrinterConnection)

    #: The OS printing subsystem will take care of spooling
    always_spools = set_default(True)

    def _default_config(self):
        if sys.platform == 'win32':
            return Win32PrinterConfig()
        else:
            return CupsPrinterConfig()

    def _default_connection(self):
        if sys.platform == 'win32':
            return Win32PrinterConnection()
        else:
            return LPRPrinterConnection()

    async def connect(self):
        try:
            # Always create a new connection
            self.connection = self._default_connection()

            # Save a reference
            self.protocol.transport = self
            self.connection.transport = self
            await self.connection.open()
            await self.connected_event.wait()
            await self.protocol.init()
            log.debug("{} | opened".format(self.config.printer))
        except Exception as e:
            # Make sure to log any issues as these tracebacks can get
            # squashed by twisted
            log.error("{} | {}".format(
                self.config.printer, traceback.format_exc()
            ))
            raise

    async def write(self, data):
        if not self.connection:
            raise IOError("Port is not opened")
        await self.connection.write(data)

    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            log.debug("{} | closed".format(self.config.printer))
            self.connection = None

    def __repr__(self):
        return self.config.printer


class PrinterPlugin(Plugin):
    """ Plugin for handling printer communication

    """

    # -------------------------------------------------------------------------
    # PrinterPlugin API
    # -------------------------------------------------------------------------

