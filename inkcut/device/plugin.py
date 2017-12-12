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
    Int, Float, observe
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

    def move(self, x, y, z, absolute=True):
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
    #: Time to wait between each step so we don't get
    #: way ahead of the cutter and fill up it's buffer
    step_time = Float(strict=False).tag(config=True)

    #: Distance between each command in user units
    #: this is effectively the resolution the software supplies
    step_size = Float(parse_unit('1mm'), strict=False).tag(config=True)

    #: Interpolate paths breaking them into small sections that
    #: can be sent. This allows pausing mid plot as many devices do not have
    #: a cancel command.
    interpolate = Bool(True).tag(config=True)

    #: How often the position will be updated in ms. Low power devices should
    #: set this to a high number like 2000 or 3000
    sample_rate = Int(100).tag(config=True)

    #: In cm/s
    speed = Float(4, strict=False)

    #: Use absolute coordinates
    absolute = Bool().tag(config=True)

    def _default_step_time(self):
        return max(1, round(
            1000* self.step_size/parse_unit('%scm' % self.speed)))


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
    declaration = Typed(extensions.DeviceDriver).tag(config=True)

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
        area = AreaBase()
        w = parse_unit(d.width)
        if d.length:
            h = parse_unit(d.length)
        else:
            h = 900000
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

    @defer.inlineCallbacks
    def test(self):
        """ Execute a test job on the device. This creates
        and submits new job that is simply a small square. 
        
        """
        raise NotImplementedError

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

    def move(self, position, absolute=True):
        """ Move to the given position. By default this delegates handling
        to the active protocol.
        
        Parameters
        ----------
            position: List of coordinates to move to. 
                Desired position to move or move to (if using absolute 
                coordinates).
            absolute: bool
                Position is in absolute coordinates
        
        Returns
        -------
            result: Deferred or None
                May return a deferred object that the process will wait for
                completion before continuing.
        
        """
        if absolute:
            print(position)
            self.position = position
        else:
            self.position = position
            p = self.position
            for i, d in enumerate(position):
                p[i] += d
            self.position = p
        result = self.connection.protocol.move(*position, absolute=absolute)
        if result:
            return result

        #: Wait for the device to catch up
        return async_sleep(self.config.step_time)

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
                for cmd in device.process(model):
                    device.handle(cmd)
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

            #: Local references are faster
            info = job.info
            connection = self.connection

            #: For tracking progress
            total_length = float(model.length())
            total_moved = 0

            #: For point in the path
            for (d, cmd, args, kwargs) in self.process(model):

                #: Check if we paused
                if info.paused:
                    self.status = "Job paused"
                    #: Sleep until resumed, cancelled, or the
                    #: connection drops
                    while (info.paused and not info.cancelled
                           and connection.connected):
                        yield async_sleep(300)  # ms

                #: Check for cancel for non interpolated jobs
                if info.cancelled:
                    self.status = "Job cancelled"
                    return
                elif not connection.connected:
                    self.status = "Connection lost"
                    return

                #: If you want to let the device handle more complex
                #: commands such as curves do it in process and handle
                yield defer.maybeDeferred(cmd, *args, **kwargs)
                total_moved += d

                #: TODO: Check if we need to update the ui
                #: Set the job progress based on how far we've gone
                info.progress = int(
                    max(0, min(100, 100*total_moved/total_length)))

        #: We're done, send any finalization commands
        yield defer.maybeDeferred(self.finish)
        #: Disconnect from the device
        yield defer.maybeDeferred(self.disconnect)

    def process(self, model):
        """  Process the path model of a job and return each command
        within the job.
        
        Parameters
        ----------
            model: QPainterPath
                The path to process
        
        Returns
        -------
            generator: A list or generator object that yields each command
             to invoke on the device and the distance moved. In the format
             (distance, cmd, args, kwargs)
        
        """
        config = self.config
        # speed = distance/seconds
        # So distance/speed = seconds to wait
        step_size = config.step_size
        if step_size <= 0:
            raise ValueError("Cannot have a step size <= 0!")
        step_time = config.step_time

        #: Previous point
        _p = QtCore.QPointF(0, 0)

        for path in model.toSubpathPolygons():

            #: And then each point within the path
            #: this is a polygon
            for i, p in enumerate(path):

                #: Head state
                # 0 move, 1 cut
                z = 0 if i == 0 else 1

                #: Make a subpath
                subpath = QtGui.QPainterPath()
                subpath.moveTo(_p)
                subpath.lineTo(p)

                #: Update the last point
                _p = p

                #: Total length
                l = subpath.length()

                #: TODO: If the device does not support streaming
                #: the path interpolation should be skipped entirely
                if not config.interpolate:
                    x, y = p.x(), -p.y()
                    yield (l, self.move, ([x, y, z],), {})
                    continue

                #: Where we are within the subpath
                d = 0

                #: Interpolate path in steps of dl and ensure we get
                #: _p and p (t=0 and t=1)
                #: This allows us to cancel mid point
                while d <= l:

                    #: Now find the point at the given step size
                    #: the first point d=0 so t=0, the last point d=l so t=1
                    t = subpath.percentAtLength(d)
                    sp = subpath.pointAtPercent(t)
                    #if d == l:
                    #    break  #: Um don't we want to send the last point??

                    #: -y because Qt's axis is from top to bottom not bottom
                    #: to top
                    x, y = sp.x(), -sp.y()
                    yield (l*t, self.move, ([x, y, z],), {})

                    #: RPI is SLOOWWW
                    #update += 1
                    #if update > 1000:
                    #    update = 0
                    #    self.position = [x, y, z]


                    #: Since sending is way faster than cutting
                    #: we must delay (without blocking the UI) before
                    #: sending the next command or the device's buffer
                    #: quickly gets filled and crappy china piece cutters
                    #: get all jacked up
                    #if step_time:
                    #yield async_sleep(0.0000001)

                    #: When we reached the end
                    if d == l:
                        #: We reached the end
                        break

                    #: Now set d to the next point by step_size
                    #: if the end of the path is less than the step size
                    #: use the minimum of the two
                    dl = min(l-d, step_size)
                    d += dl


    # @defer.inlineCallbacks
    # def handle(self, cmd, *args, **kwargs):
    #     """ Handle a command from the model. By default this just
    #
    #     Parameters
    #     ----------
    #     commmand: Tuple of Command to handle such as a
    #
    #     """
    #     yield defer.maybeDeferred(cmd, *args, **kwargs)


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

        #: This refreshes everything else
        self._refresh_extensions()

        #: Restore state after plugins are loaded
        super(DevicePlugin, self).start()

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

    # -------------------------------------------------------------------------
    # Live progress API
    # -------------------------------------------------------------------------
    @observe('device.job')
    def _reset_preview(self, change):
        """ Redraw the preview on the screen 
        
        """
        log.info(change)
        view_items = []

        #: Transform used by the view
        preview_plugin = self.workbench.get_plugin('inkcut.preview')
        plot = preview_plugin.live_preview
        t = preview_plugin.transform

        #: Draw the device
        device = self.device
        job = device.job
        if device and device.area:
            area = device.area
            view_items.append(
                dict(path=device.area.path*t, pen=plot.pen_device,
                     skip_autorange=(False, [area.size[0], 0]))
            )

        #: The model is only set when a document is open and has no errors
        if job and job.model:
            view_items.extend([
                dict(path=job.move_path, pen=plot.pen_up),
                dict(path=job.cut_path, pen=plot.pen_down)
            ])
            #: TODO: This
            #if self.show_offset_path:
            #    view_items.append(PainterPathPlotItem(
            # self.job.offset_path,pen=self.pen_offset))
        if job and job.material:
            # Also observe any change to job.media and job.device
            view_items.extend([
                dict(path=job.material.path*t, pen=plot.pen_media,
                     skip_autorange=(False, [0, job.size[1]])),
                dict(path=job.material.padding_path*t,
                     pen=plot.pen_media_padding, skip_autorange=True)
            ])

        #: Update the plot
        preview_plugin.set_live_preview(*view_items)

    @observe('device.position')
    def _update_preview(self, change):
        """ Watch the position of the device as it changes. """
        if change['type'] == 'update' and self.device.job:
            x, y, z = change['value']
            preview_plugin = self.workbench.get_plugin('inkcut.preview')
            preview_plugin.live_preview.update(change['value'])