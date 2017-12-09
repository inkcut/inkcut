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
    Typed, List, Instance, ForwardInstance, ContainerList, Bool, Unicode,
    Float, observe
)
from contextlib import contextmanager
from enaml.qt import QtCore, QtGui
from inkcut.core.api import Model, Plugin, AreaBase
from inkcut.core.utils import parse_unit, async_sleep, log
from twisted.internet import defer
from . import extensions


class DeviceTransport(Model):

    #: The declaration that defined this transport
    declaration = Typed(extensions.DeviceTransport).tag(config=True)

    #: The transport specific config
    config = Instance(Model, ()).tag(config=True)

    #: The active protocol
    protocol = ForwardInstance(lambda: DeviceProtocol).tag(config=True)

    #: Connection state. Subclasses must implement and properly update this
    connected = Bool()

    def connect(self):
        """ Connect using whatever implementation necessary
        
        """
        raise NotImplementedError

    def write(self, data):
        """ Write using whatever implementation necessary
        
        """
        raise NotImplementedError

    def read(self, size=None):
        """ Read using whatever implementation necessary.
        
        """
        raise NotImplementedError

    def disconnect(self):
        """ Disconnect using whatever implementation necessary
        
        """
        raise NotImplementedError


class DeviceProtocol(Model):

    #: The declaration that defined this protocol
    declaration = Typed(extensions.DeviceProtocol).tag(config=True)

    #: The active protocol
    transport = Instance(DeviceTransport)

    #: The protocol specific config
    config = Instance(Model, ()).tag(config=True)

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
    #: Time between each path command
    step_time = Float()

    #: Distance between each step
    step_size = Float()

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
    connection = Instance(DeviceTransport).tag(config=True)

    #: List of jobs run on this device
    jobs = List(Model).tag(config=True)

    #: Current job being processed
    job = Instance(Model).tag(config=True)

    #: The device specific config
    config = Instance(Model, factory=DeviceConfig).tag(config=True)

    #: Position. Defaults to x,y,z. The protocol can
    #: handle this however necessary.
    position = ContainerList(default=[0, 0, 0])

    #: Device is currently busy processing a job
    busy = Bool()

    #: Status
    status = Unicode()

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

    @contextmanager
    def device_busy(self):
        self.busy = True
        try:
            yield
        finally:
            self.busy = False

    def init(self, job):
        """ Initialize the job 
        
        Parameters
        -----------
            job: inkcut.job.models.Job instance
                The job to handle. 
        
        Returns
        --------
            model: QtGui.QPainterPath instance or Deferred that resolves
                to a QPainterPath if heavy processing is needed. This path
                is then interpolated and sent to the device. 
        
        """
        self.job = job

        #: TODO: Allow plugins to hook into this

        return job.model

    def connect(self):
        """ Connect to the device. By default this delegates handling
        to the active transport or connection handler. 
         
        Returns
        -------
            result: Deferred or None
                May return a Deferred object that the process will wait for
                completion before continuing.
        
        """
        return self.connection.connect()

    def disconnect(self):
        """ Disconnect from the device. By default this delegates handling
        to the active transport or connection handler. 
        
        """
        return self.connection.disconnect()

    @defer.inlineCallbacks
    def submit(self, job):
        """ Submit the job to the device. This handles iteration over the
        path model defined by the job and sending commands to the actual
        device using roughly the procedure is as follows:
                
                device.connect()
                
                model = device.init(job)
                for p in model:
                    device.move(*p)
                device.finish()
                
                device.disconnect()
        
        Subclasses provided by your own DeviceDriver may reimplement this
        to handle path interpolation however needed. The return value is
        ignored.
        
        The live plot view will update whenever the device.position object
        is updated. On devices with lower cpu/gpu capabilities this should
        be updated sparingly (ie the raspberry pi).
        
        Parameters
        -----------
            job: Instance of `inkcut.job.models.Job`
                The job to execute on the device
                
        """
        #: Only allow one job at a time
        if self.busy:
            raise RuntimeError("Device is busy processing another job!")

        with self.device_busy():
            self.status = "Connecting to device"

            #: Connect
            yield defer.maybeDeferred(self.connect)

            self.status = "Initializing job"

            # Device model is updated in real time
            model = yield defer.maybeDeferred(self.init, job)

            self.status = "Processing job"
            x, y, z = self.position  # get the initial state
            _x, _y = x, y

            #speed = self.device.speed # Units/second
            # device.speed is in CM/s
            # d is in PX so...
            # speed = distance/seconds
            # So distance/speed = seconds to wait

            #: Distance between each command in user units
            #: this is effectively the resolution the software supplies
            step_size = self.step_size

            #: Time to wait between each step so we don't get
            #: way ahead of the cutter and fill up it's buffer
            step_time = self.step_time


            #: Total length
            total_length = float(job.model.length())
            #: How far we went already
            total_moved = 0

            #: Previous point
            _p = QtCore.QPointF(0, 0)

            self.status = "Job length: {}".format(total_length)

            update = 0

            #: For each path
            for path in model.toSubpathPolygons():

                #: And then each point within the path
                #: this is a polygon
                for i, p in enumerate(path):

                    #: TODO: If the device does not support streaming
                    #: the path interpolation should be skipped entirely

                    #: Make a subpath
                    subpath = QtGui.QPainterPath()
                    subpath.moveTo(_p)
                    subpath.lineTo(p)

                    #: Head state
                    z = self.PEN_UP if i == 0 else self.PEN_DOWN # 0 move, 1 cut

                    #: Where we are within the subpath
                    d = 0

                    #: Total length
                    l = subpath.length()

                    #: Interpolate path in steps of dl and ensure we get _p and p (t=0 and t=1)
                    #: This allows us to cancel mid point

                    while d <= l:  # and self.isVisible():
                        if job.info.cancelled:
                            self.status = "Job cancelled"
                            return
                        if job.info.paused:
                            self.status = "Job paused"
                            yield async_sleep(1000)  # ms
                            continue  # Keep waiting...
                        if not self.connection.connected:
                            self.status = "Connection lost"
                            return

                        #: Now find the point at the given step size
                        #: the first point d=0 so t=0, the last point d=l so t=1
                        sp = subpath.pointAtPercent(subpath.percentAtLength(d))
                        #if d == l:
                        #    break  #: Um don't we want to send the last point??

                        #: -y because Qt's axis is from top to bottom not bottom to top
                        x, y = sp.x(), -sp.y()
                        yield defer.maybeDeferred(self.move, x, y, z)

                        #: RPI is SLOOWWW
                        update += 1
                        if update > 1000:
                            update = 0
                            self.position = [x, y, z]

                            #: Set the job progress based on how far we've gone
                            job.info.progress = int(max(0,min(100, 100*total_moved/total_length)))

                        #: Since sending is way faster than cutting
                        #: we must delay (without blocking the UI) before
                        #: sending the next command or the device's buffer
                        #: quickly gets filled and crappy china piece cutters
                        #: get all jacked up
                        #if step_time:
                        yield async_sleep(0.0000001)

                        #: When we reached the end
                        if d == l:
                            #: We reached the end
                            break

                        #: Now set d to the next point by step_size
                        #: if the end of the path is less than the step size
                        #: use the minimum of the two
                        dl = min(l-d, step_size)
                        total_moved += dl
                        d += dl

                    #: Update the last point
                    _p = p

        #: We're done, send any finalization commands
        yield defer.maybeDeferred(self.finish)
        #: Disconnect from the device
        yield defer.maybeDeferred(self.disconnect)

    def _observe_status(self, change):
        """ Whenever the status changes, log it """
        log.info("Device: {}".format(self.status))


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
    devices = List(Device).tag(config=True)

    #: Current device
    device = Instance(Device).tag(config=True)

    # -------------------------------------------------------------------------
    # Plugin API
    # -------------------------------------------------------------------------
    def start(self):
        """ Load all the plugins the device is dependent on """
        w = self.workbench
        with enaml.imports():
            #: TODO autodiscover these
            from inkcut.device.serialport.manifest import SerialManifest
            from inkcut.device.protocols.manifest import ProtocolManifest
            from inkcut.device.drivers.manifest import DriversManifest
            from inkcut.device.pi.manifest import PiManifest
            w.register(SerialManifest())
            w.register(ProtocolManifest())
            w.register(DriversManifest())
            w.register(PiManifest())

        #: Restore state after plugins are loaded
        super(DevicePlugin, self).start()

        #: This refreshes everything else
        self._refresh_extensions()

    # def _default_devices(self):
    #     """ Load the devices supported """
    #     self._refresh_drivers()
    #     return self.devices[0]

    # def _observe_device(self, change):
    #     """ When the device changes, save it. """
    #     devices = self.devices[:]
    #     if self.device not in devices:
    #         devices.append(self.device)
    #     self.devices = devices

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

    # -------------------------------------------------------------------------
    # Device Driver API
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Device Extensions API
    # -------------------------------------------------------------------------
    def _refresh_extensions(self):
        """ Refresh all extensions provided by the DevicePlugin """
        self._refresh_protocols()
        self._refresh_transports()
        self._refresh_drivers()

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