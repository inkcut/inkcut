# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 19, 2017

@author: jrm
"""
import sys
import traceback
from atom.api import List, Instance, Unicode
from inkcut.core.api import Plugin, Model, log
from inkcut.device.plugin import DeviceTransport
from twisted.internet import reactor
from twisted.internet.protocol import ProcessProtocol

try:
    if sys.platform == 'win32':
        import win32print
    elif sys.platform == 'darwin':
        pass
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
    printer = Unicode().tag(config=True)

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

    def open(self):
        raise NotImplementedError

    def write(self, data):
        log.debug("-> {} | {}".format(self.transport.config.printer, data))

    def close(self):
        raise NotImplementedError


# -----------------------------------------------------------------------------
# Windows API
# -----------------------------------------------------------------------------
class Win32PrinterConfig(PrinterConfig):

    def _default_printers(self):
        if not PRINTER_AVAILABLE:
            return []
        return [p.Name for p in win32print.EnumPrinters()]


class Win32PrinterConnection(PrinterConnection):
    job = Instance(object)

    def open(self):
        p = win32print.OpenPrinter(self.transport.config.printer)
        self.job = win32print.StartDocPrinter(
            p, 1, ("Inkcut job", None, "RAW"))
        win32print.StartPagePrinter(p)
        self.printer = p

        #: Sync
        self.transport.connected = True
        self.transport.protocol.connection_made()

    def write(self, data):
        super(Win32PrinterConnection, self).write(data)
        win32print.WritePrinter(self.printer, data)

    def close(self):
        p = self.printer
        win32print.EndPagePrinter(p)
        win32print.EndDocPrinter(p)
        win32print.ClosePrinter(p)
        #: Sync
        self.transport.connected = False
        self.transport.protocol.connection_lost()


# -----------------------------------------------------------------------------
# Cups API
# -----------------------------------------------------------------------------
class CupsPrinterConfig(PrinterConfig):

    def _default_printers(self):
        if not PRINTER_AVAILABLE:
            return []
        return list(cups.Connection().getPrinters().keys())


# -----------------------------------------------------------------------------
# LPR API
# -----------------------------------------------------------------------------
class LPRProtocol(ProcessProtocol):
    def __init__(self, parent, protocol):
        self.parent = parent
        self.parent.connected = True
        self.delegate = protocol

    def connectionMade(self):
        self.delegate.connection_made()

    def outReceived(self, data):
        self.delegate.data_received(data)

    def inReceived(self, data):
        self.delegate.data_received(data)

    def processEnded(self, reason):
        self.parent.connected = False
        self.delegate.connection_lost()


class LPRPrinterConnection(PrinterConnection):
    #: Delegate
    _protocol = Instance(LPRProtocol)

    def open(self):
        t = self.transport
        self._protocol = LPRProtocol(t, t.protocol)
        self.printer = reactor.spawnProcess(
            self._protocol, 'lpr', ['lpr', '-P', t.config.printer]
        )

    def write(self, data):
        super(LPRPrinterConnection, self).write(data)
        if hasattr(data, 'encode'):
            data = data.encode()
        self._protocol.transport.write(data)

    def close(self):
        #: Close, the process should exit
        self._protocol.transport.closeStdin()


# -----------------------------------------------------------------------------
# Inkcut API
# -----------------------------------------------------------------------------
class PrinterTransport(DeviceTransport):

    #: Default config
    config = Instance(PrinterConfig).tag(config=True)

    #: Delegate to the implementation based on the current platform
    connection = Instance(PrinterConnection)

    def _default_config(self):
        if sys.platform == 'win32':
            return Win32PrinterConfig()
        elif sys.platform == 'darwin':
            raise NotImplementedError
        else:
            return CupsPrinterConfig()

    def _default_connection(self):
        if sys.platform == 'win32':
            return Win32PrinterConnection()
        else:
            return LPRPrinterConnection()

    def connect(self):
        try:
            # Always create a new connection
            self.connection = self._default_connection()

            # Save a reference
            self.protocol.transport = self
            self.connection.transport = self
            self.connection.open()
            log.debug("{} | opened".format(self.config.printer))
        except Exception as e:
            # Make sure to log any issues as these tracebacks can get
            # squashed by twisted
            log.error("{} | {}".format(
                self.config.printer, traceback.format_exc()
            ))
            raise

    def write(self, data):
        if not self.connection:
            raise IOError("Port is not opened")
        self.connection.write(data)

    def disconnect(self):
        if self.connection:
            self.connection.close()
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

