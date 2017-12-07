# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jan 16, 2015

@author: jrm
"""
import enaml
from atom.api import List, Instance, Unicode
from inkcut.core.api import Model, Plugin


class DeviceProtocol(Model):
    #: Display name for this protocol
    name = Unicode()

    def connection_made(self):
        """ This is called when a connection is made to the device. 
         
        Use this to send any initialization commands before the job starts.
        
        """

    def set_pen(self, p):
        """ Set the pen or tool that should be used.
         
         Parameters
        ----------
        p: int
            The pen or tool number to use.
        
        """

    def set_force(self, f):
        """ Set the force the device should use.
        
        Parameters
        ----------
        f: int
            The force setting value to send to the device

        """

    def set_velocity(self, v):
        """ Set the force the device should use.

        Parameters
        ----------
        v: int
            The force setting value to send to the device
        
        """

    def write(self, data):
        """ Call this to write data using the underlying transport.
        
        This should typically not be overridden. 
        
        """

    def data_received(self, data):
        """ Called when the device replies back with data. This can occur
        at any time as communication is asynchronous. The protocol should
        handle as needed.s
        
        Parameters
        ----------
        data


        """

    def finish(self):
        """ Called when processing all of the paths of the job are complete.
        
        Use this to send any finalization commands.
        
        """

    def connection_lost(self):
        """ Called the connection to the device is dropped or
        failed to connect.  No more data can be written when this is called.
        
        """


class Device(DeviceProtocol):
    """ The standard device. It simply delegates to the given 
    protocol.
    
    """
    #: Protocols supported by this device
    protocols = List(DeviceProtocol)

    #: The selected protocol
    protocol = Instance(DeviceProtocol)

    def connection_made(self):
        self.protocol.connection_made()

    def set_pen(self, p):
        self.protocol.set_pen(p)

    def set_velocity(self, v):
        self.protocol.set_velocity(v)

    def write(self, data):
        self.protocol.write(data)

    def connection_lost(self):
        self.protocol.connection_lost()


class DevicePlugin(Plugin):
    """ Plugin for configuring, using, and communicating with 
    a device.
    
    """

    #: Devices configured
    devices = List(DeviceProtocol)

    #: Current device
    device = Instance(Device, ())

    def start(self):
        """ Load all the plugins the device is dependent on """
        w = self.workbench
        with enaml.imports():
            #: TODO autodiscover these
            from inkcut.device.serialport.manifest import SerialManifest
            from inkcut.device.protocols.manifest import ProtocolManifest
            w.register(SerialManifest())
            w.register(ProtocolManifest())