# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jan 16, 2015

@author: jrm
"""
import enaml
from atom.api import (
    Typed, List, Instance, ForwardInstance, ContainerList, Bool,  observe
)
from inkcut.core.api import Model, Plugin, AreaBase, parse_unit
from . import extensions


class DeviceTransport(Model):

    #: The declaration that defined this transport
    declaration = Typed(extensions.DeviceTransport)

    #: The transport specific config
    config = Instance(Model, ())

    #: The active protocol
    protocol = ForwardInstance(lambda: DeviceProtocol)

    def connect(self):
        protocol = self.protocol
        protocol.transport = self
        protocol.connection_made()

    def write(self, data):
        raise NotImplementedError

    def read(self, size=None):
        raise NotImplementedError

    def disconnect(self):
        self.protocol.connection_lost()


class DeviceProtocol(Model):

    #: The declaration that defined this protocol
    declaration = Typed(extensions.DeviceProtocol)

    #: The active protocol
    transport = Instance(DeviceTransport)

    #: The protocol specific config
    config = Instance(Model, ())

    def connection_made(self):
        """ This is called when a connection is made to the device. 
         
        Use this to send any initialization commands before the job starts.
        
        """
        raise NotImplementedError

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

    def move(self, x, y, z):
        """ Called when the device position is updated.
        
        """
        raise NotImplementedError

    def write(self, data):
        """ Call this to write data using the underlying transport.
        
        This should typically not be overridden. 
        
        """
        self.transport.write(data)

    def data_received(self, data):
        """ Called when the device replies back with data. This can occur
        at any time as communication is asynchronous. The protocol should
        handle as needed.s
        
        Parameters
        ----------
        data


        """
        raise NotImplementedError

    def finish(self):
        """ Called when processing all of the paths of the job are complete.
        
        Use this to send any finalization commands.
        
        """
        raise NotImplementedError

    def connection_lost(self):
        """ Called the connection to the device is dropped or
        failed to connect.  No more data can be written when this is called.
        
        """
        raise NotImplementedError


class DeviceConfig(Model):
    """ The default device configuration. Custom devices may want to subclass 
    this. 
    
    """


class Device(Model):
    """ The standard device. This is a standard model used throughout the
    application. An instance of this is configured by specifying a 
    'DeviceDriver' in a plugin manifest. 
    
    It simply delegates connection and handling to the selected transport
    and protocol respectively.
    
    """

    #: Internal model for drawing the preview on screen
    area = Instance(AreaBase)

    #: The declaration that defined this device
    declaration = Typed(extensions.DeviceDriver)

    #: Protocols supported by this device (ex the HPGLProtocol)
    protocols = List(extensions.DeviceProtocol)

    #: Transports supported by this device (ex the SerialPort
    transports = List(extensions.DeviceTransport)

    #: The active transport
    connection = Instance(DeviceTransport)

    #: The device specific config
    config = Instance(Model, factory=DeviceConfig)

    #: Position. Defaults to x,y,z. The protocol can
    #: handle this however necessary.
    position = ContainerList(default=[0, 0, 0])

    #: Connected
    connected = Bool()

    def _default_connection(self):
        if not self.transports:
            return None
        declaration = self.transports[0]
        transport = declaration.factory()
        transport.declaration = declaration
        transport.protocol = self._default_protocol()
        return transport

    def _default_protocol(self):
        if not self.protocols:
            return None
        declaration = self.protocols[0]
        protocol = declaration.factory()
        protocol.declaration = declaration
        return protocol

    def _default_area(self):
        """ Create the area based on the size specified by the Device Driver
        
        """
        d = self.declaration
        w = parse_unit(d.width)
        if d.length:
            h = parse_unit(d.length)
        else:
            h = 900000

        area = AreaBase()
        area.size = [w, h]
        return area

    @observe('declaration.width', 'declaration.length')
    def _refresh_area(self, change):
        self.area = self._default_area()

    # def init(self):
    #     self.transport.connect()
    #
    #
    # def finish(self):
    #     self.transport.disconnect()
    #
    # def _observe_connected(self, change):
    #     if change['type'] == 'create':
    #         return
    #     if self.connected:
    #         self.protocol.connnection_made()
    #     else:
    #         self.protocol.connection_lost()
    #
    # def _observe_position(self, change):
    #     """ Move to the given position
    #
    #     """
    #     if change['type'] == 'create':
    #         return
    #     self.protocol.move(*self.position)
    #
    # def _observe_config(self, change):
    #     self.protocol.configure(self.config)


class DevicePlugin(Plugin):
    """ Plugin for configuring, using, and communicating with 
    a device.
    
    """

    #: Protocols registered in the system
    protocols = List(extensions.DeviceProtocol)

    #: Transports
    transports = List(extensions.DeviceTransport)

    #: Drivers registered in the system
    drivers = List(extensions.DeviceDriver)

    #: Devices configured
    devices = List(Device)

    #: Current device
    device = Instance(Device)

    def start(self):
        """ Load all the plugins the device is dependent on """
        w = self.workbench
        with enaml.imports():
            #: TODO autodiscover these
            from inkcut.device.serialport.manifest import SerialManifest
            from inkcut.device.protocols.manifest import ProtocolManifest
            from inkcut.device.drivers.manifest import DriversManifest
            w.register(SerialManifest())
            w.register(ProtocolManifest())
            w.register(DriversManifest())

        #: This refreshes everything else
        self._refresh_extensions()

    # def _default_devices(self):
    #     """ Load the devices supported """
    #     self._refresh_drivers()
    #     return self.devices[0]

    def _refresh_extensions(self):
        """ Refresh all extensions provided by the DevicePlugin """
        self._refresh_protocols()
        self._refresh_transports()
        self._refresh_drivers()

    def _default_device(self):
        """ If no device is loaded from the previous state, get the device
        from the first driver loaded.
        
        """
        self._refresh_extensions()

        #: If a device is configured, use that
        if self.devices:
            return self.devices[0]

        #: Otherwise create one using the first registered driver
        if not self.drivers:
            raise RuntimeError("No device drivers were registered. "
                               "This indicates a missing plugin.")
        return self.get_device_from_driver(self.drivers[0])

    def get_device_from_driver(self, driver):
        """ Load the device driver. This generates the device using
        the factory function the DeviceDriver specifies and assigns
        the protocols and transports based on the filters given by
        the driver.
        
        Parameters
        ----------
            driver: inkcut.device.extensions.DeviceDriver
                The DeviceDriver declaration to use to create a device.
        Returns
        -------
            device: inkcut.device.plugin.Device
                The actual device object that will be used for communication
                and processing the jobs.
        
        """
        #: Generate the device
        device = driver.factory()

        #: Now set the declaration
        device.declaration = driver

        #: Set the protocols based on the declaration
        if driver.protocols:
            device.protocols = [p for p in self.protocols
                                if p.id in driver.protocols]
        else:
            device.protocols = self.protocols[:]

        #: Set the protocols based on the declaration
        if driver.connections:
            device.transports = [t for t in self.transports
                                 if t.id in driver.connections]
        else:
            device.transports = self.transports[:]

        return device

    def _refresh_protocols(self):
        """ Reload all DeviceProtocols registered by any Plugins 
        
        Any plugin can add to this list by providing a DeviceProtocol 
        extension in the PluginManifest.
        
        """
        workbench = self.workbench
        point = workbench.get_extension_point(extensions.DEVICE_PROTOCOL_POINT)

        protocols = []
        for extension in sorted(point.extensions, key=lambda ext: ext.rank):
            for p in extension.get_children(extensions.DeviceProtocol):
                protocols.append(p)

        #: Update
        self.protocols = protocols

    def _refresh_transports(self):
        """ Reload all DeviceTransports registered by any Plugins 
        
        Any plugin can add to this list by providing a DeviceTransport 
        extension in the PluginManifest.
        
        """
        workbench = self.workbench
        point = workbench.get_extension_point(
            extensions.DEVICE_TRANSPORT_POINT)

        transports = []
        for extension in sorted(point.extensions, key=lambda ext: ext.rank):
            for t in extension.get_children(extensions.DeviceTransport):
                transports.append(t)

        #: Update
        self.transports = transports

    def _refresh_drivers(self):
        """ Reload all DeviceDrivers registered by any Plugins 
        
        Any plugin can add to this list by providing a DeviceDriver 
        extension in the PluginManifest.
        
        """
        workbench = self.workbench
        point = workbench.get_extension_point(extensions.DEVICE_DRIVER_POINT)
        drivers = []
        for extension in sorted(point.extensions, key=lambda ext: ext.rank):
            for driver in extension.get_children(extensions.DeviceDriver):
                if not driver.id:
                    driver.id = "{} {}".format(driver.manufacturer,
                                               driver.model)
                drivers.append(driver)

        #: Update
        self.drivers = drivers