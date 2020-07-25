# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jan 16, 2015

@author: jrm
"""
import enaml
import traceback
from atom.api import (
    Typed, List, Instance, ForwardInstance, ContainerList, Bool, Unicode,
    Int, Float, Enum, Bytes, observe
)
from contextlib import contextmanager
from datetime import datetime
from enaml.qt import QtCore, QtGui
from enaml.application import timed_call
from inkcut.core.api import Model, Plugin, AreaBase
from inkcut.core.utils import parse_unit, from_unit, to_unit, async_sleep, log
from twisted.internet import defer
from io import BytesIO
from . import extensions


class DeviceError(AssertionError):
    """ Error for whatever """


class DeviceTransport(Model):

    #: The declaration that defined this transport
    declaration = Typed(extensions.DeviceTransport).tag(config=True)

    #: The transport specific config
    config = Instance(Model, ()).tag(config=True)

    #: The active protocol
    protocol = ForwardInstance(lambda: DeviceProtocol).tag(config=True)

    #: Connection state. Subclasses must implement and properly update this
    connected = Bool()

    #: Distinguish between transports that always spool (e.g. Printer, File I/O)
    #: or are dependent on the 'spooling' configuration option (e.g. Serial)
    always_spools = Bool()

    #: Most recent input/output. These can be observed to update the UI
    last_read = Bytes()
    last_write = Bytes()

    def __init__(self, *args, **kwargs):
        super(DeviceTransport, self).__init__(*args, **kwargs)
        if self.protocol:
            self.protocol.transport = self

    def _observe_protocol(self, change):
        """ Whenever the protocol changes update the transport reference

        """
        if change['type'] in ('update', 'create') and change['value']:
            self.protocol.transport = self

    def connect(self):
        """ Connect using whatever implementation necessary

        """
        raise NotImplementedError

    def write(self, data):
        """ Write using whatever implementation necessary

        """
        raise NotImplementedError

    def read(self, size=None):
        """ Read using whatever implementation necessary and
        invoke `protocol.data_received` with the output.

        """
        raise NotImplementedError

    def disconnect(self):
        """ Disconnect using whatever implementation necessary

        """
        raise NotImplementedError


class TestTransport(DeviceTransport):
    """ A transport that captures protocol output """

    #: The output buffer
    buffer = Instance(BytesIO, ())

    def connect(self):
        self.connected = True
        #: Save a reference
        self.protocol.transport = self
        self.protocol.connection_made()

    def write(self, data):
        log.debug("-> Test | {}".format(data))

        #: Python 3 is annoying
        if hasattr(data, 'encode'):
            data = data.encode()

        self.buffer.write(data)

    def read(self, size=None):
        return ""

    def disconnect(self):
        self.connected = False
        self.protocol.connection_lost()


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
        if self.transport is not None:
            self.transport.write(data)

    def data_received(self, data):
        """ Called when the device replies back with data. This can occur
        at any time as communication is asynchronous. The protocol should
        handle as needed.

        Parameters
        ----------
        data


        """
        log.debug("data received: {}".format(data))

    def finish(self):
        """ Called when processing all of the paths of the job are complete.

        Use this to send any finalization commands.

        """
        pass

    def connection_lost(self):
        """ Called the connection to the device is dropped or
        failed to connect.  No more data can be written when this is called.

        """
        pass


class DeviceFilter(Model):
    """ A device filter is applied to apply either the QPainterPath or to the
    list of polygons generated when the path is converted to simple move
    and line segments.

    """

    #: The declaration that defined this filter
    declaration = Typed(extensions.DeviceFilter).tag(config=True)

    #: The protocol specific config
    config = Instance(Model, ()).tag(config=True)

    def apply_to_model(self, model, job):
        """ Apply the filter to the model

        Parameters
        ----------
        model: QPainterPath
            The path model to process
        job: inkcut.device.Job
            The job this is coming from

        Returns
        -------
        model: QPainterPath
            The path model with the filter applied

        """
        return model

    def apply_to_polypath(self, polypath):
        """ Apply the filter to the model

        Parameters
        ----------
        polypath: List of QPolygon
            List of polygons to process

        Returns
        -------
        polypath: List of QPolygon
            List of polygons with the filter applied

        """
        return polypath


class DeviceConfig(Model):
    """ The default device configuration. Custom devices may want to subclass
    this.

    """
    #: Time between each path command
    #: Time to wait between each step so we don't get
    #: way ahead of the cutter and fill up it's buffer
    step_time = Float(strict=False).tag(config=True)
    custom_rate = Float(-1, strict=False).tag(config=True)

    #: Distance between each command in user units
    #: this is effectively the resolution the software supplies
    step_size = Float(parse_unit('1mm'), strict=False).tag(config=True)

    #: Interpolate paths breaking them into small sections that
    #: can be sent. This allows pausing mid plot as many devices do not have
    #: a cancel command.
    interpolate = Bool(False).tag(config=True)

    #: How often the position will be updated in ms. Low power devices should
    #: set this to a high number like 2000 or 3000
    sample_rate = Int(100).tag(config=True)

    #: Final output rotation
    rotation = Enum(0, 90, -90).tag(config=True)

    #: Swap x and y axis
    swap_xy = Bool().tag(config=True)
    mirror_y = Bool().tag(config=True)
    mirror_x = Bool().tag(config=True)

    #: Final out scaling
    scale = ContainerList(Float(strict=False), default=[1, 1]).tag(config=True)

    #: Defines prescaling before conversion to a polygon
    quality_factor = Float(1, strict=False).tag(config=True)

    #: In cm/s
    speed = Float(4, strict=False).tag(config=True)
    speed_units = Enum('in/s', 'cm/s').tag(config=True)
    speed_enabled = Bool().tag(config=True)

    #: Force in g
    force = Float(40, strict=False).tag(config=True)
    force_units = Enum('g').tag(config=True)
    force_enabled = Bool().tag(config=True)

    #: Use absolute coordinates
    absolute = Bool().tag(config=True)

    #: Device output is spooled by an external service
    #: this will cause the job to run with no delays between commands
    spooled = Bool().tag(config=True)

    #: Use a virtual connection
    test_mode = Bool().tag(config=True)

    #: Init commands
    commands_before = Unicode().tag(config=True)
    commands_after = Unicode().tag(config=True)
    commands_connect = Unicode().tag(config=True)
    commands_disconnect = Unicode().tag(config=True)

    def _default_step_time(self):
        """ Determine the step time based on the device speed setting


        """
        #: Convert speed to px/s then to mm/s
        units = self.speed_units.split("/")[0]
        speed = parse_unit('%s%s' % (self.speed, units))
        speed = to_unit(speed, 'mm')
        if speed == 0:
            return 0

        #: No determine the time and convert to ms
        return max(0, round(1000*self.step_size/speed))

    @observe('speed', 'speed_units', 'step_size')
    def _update_step_time(self, change):
        if change['type'] == 'update':
            self.step_time = self._default_step_time()


class Device(Model):
    """ The standard device. This is a standard model used throughout the
    application. An instance of this is configured by specifying a
    'DeviceDriver' in a plugin manifest.

    It simply delegates connection and handling to the selected transport
    and protocol respectively.

    """
    #: Display Items
    name = Unicode("New device").tag(config=True)
    manufacturer = Unicode().tag(config=True)
    model = Unicode().tag(config=True)
    custom = Bool().tag(config=True)

    #: Internal model for drawing the preview on screen
    area = Instance(AreaBase)

    #: The declaration that defined this device
    declaration = Typed(extensions.DeviceDriver).tag(config=True)

    #: Protocols supported by this device (ex the HPGLProtocol)
    protocols = List(extensions.DeviceProtocol)

    #: Transports supported by this device (ex the SerialPort
    transports = List(extensions.DeviceTransport)

    #: Filters that this device applies to the output
    filters = List(DeviceFilter).tag(config=True)

    #: The active transport
    connection = Instance(DeviceTransport).tag(config=True)

    #: List of jobs that were run on this device
    jobs = List(Model).tag(config=True)

    #: List of jobs queued to run on this device
    queue = List(Model).tag(config=True)

    #: Current job being processed
    job = Instance(Model)#.tag(config=True)

    #: The device specific config
    config = Instance(DeviceConfig, ()).tag(config=True)

    #: Position. Defaults to x,y,z. The protocol can
    #: handle this however necessary.
    position = ContainerList(default=[0, 0, 0])

    #: Origin position. Defaults to [0, 0, 0]. The system will translate
    #: jobs to the origin so multiple can be run.
    origin = ContainerList(default=[0, 0, 0])

    #: Device is currently busy processing a job
    busy = Bool()

    #: Status
    status = Unicode()

    def _default_connection(self):
        """ If no connection is set when the device is created,
        create one using the first "connection" type the driver supports.
        """
        if not self.transports:
            return TestTransport()
        declaration = self.transports[0]
        driver = self.declaration
        protocol = self._default_protocol()
        return declaration.factory(driver, declaration, protocol)

    def _default_protocol(self):
        """ Create the protocol for this device. """
        if not self.protocols:
            return DeviceProtocol()
        declaration = self.protocols[0]
        driver = self.declaration
        return declaration.factory(driver, declaration)

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
        """ Mark the device as busy """
        self.busy = True
        try:
            yield
        finally:
            self.busy = False

    @contextmanager
    def device_connection(self, test=False):
        """ """
        connection = self.connection
        try:
            #: Create a test connection if necessary
            if test:
                self.connection = TestTransport(
                    protocol=connection.protocol,
                    declaration=connection.declaration
                )
            #: Connect
            yield self.connection
        finally:
            #: Restore if necessary
            if test:
                self.connection = connection

    @defer.inlineCallbacks
    def test(self):
        """ Execute a test job on the device. This creates
        and submits new job that is simply a small square.

        """
        raise NotImplementedError

    def transform(self, path):
        """ Apply the device output transform to the given path. This
        is used by other plugins that may need to display or work with
        tranformed output.

        Parameters
        ----------
            path: QPainterPath
                Path to transform

        Returns
        -------
            path: QPainterPath

        """
        config = self.config

        t = QtGui.QTransform()

        #: Order matters!
        if config.scale:
            #: Do final output scaling
            t.scale(*config.scale)

        if config.rotation:
            #: Do final output rotation
            t.rotate(config.rotation)

        #: TODO: Translate back to 0,0 so all coordinates are positive
        path = path * t

        return path

    def init(self, job):
        """ Initialize the job. This should do any final path manipulation
        required by the device (or as specified by the config) and any filters
        should be applied here (overcut, blade offset compensation, etc..).

        The connection is not active at this stage.

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
        log.debug("device | init {}".format(job))
        config = self.config

        # Set the speed of this device for tracking purposes
        units = config.speed_units.split("/")[0]
        job.info.speed = from_unit(config.speed, units)

        scale = config.scale[:]
        if config.mirror_x:
            scale[0] *= -1 if config.mirror_x else 1
        if config.mirror_y:
            scale[1] *= -1 if config.mirror_y else 1

        # Get the internal QPainterPath "model" transformed to how this
        # device outputs
        model = job.create(swap_xy=config.swap_xy, scale=scale)

        if job.feed_to_end:
            #: Move the job to the new origin
            x, y, z = self.origin
            model.translate(x, -y)

        #: TODO: Apply filters here

        #: Return the transformed model
        return model

    @defer.inlineCallbacks
    def connect(self):
        """ Connect to the device. By default this delegates handling
        to the active transport or connection handler.

        Returns
        -------
            result: Deferred or None
                May return a Deferred object that the process will wait for
                completion before continuing.

        """
        log.debug("device | connect")
        yield defer.maybeDeferred(self.connection.connect)
        cmd = self.config.commands_connect
        if cmd:
            yield defer.maybeDeferred(self.connection.write, cmd)

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
            #: Clip everything to never go below zero in absolute mode
            position = [max(0, p) for p in position]
            self.position = position
        else:
            #: Convert to relative to absolute for the UI
            p = self.position
            p[0] += position[0]
            p[1] += position[1]
            self.position = p

        result = self.connection.protocol.move(*position, absolute=absolute)
        if result:
            return result

    def finish(self):
        """ Finish the job applying any cleanup necessary.

        """
        log.debug("device | finish")
        return self.connection.protocol.finish()

    @defer.inlineCallbacks
    def disconnect(self):
        """ Disconnect from the device. By default this delegates handling
        to the active transport or connection handler.

        """
        log.debug("device | disconnect")
        cmd = self.config.commands_disconnect
        if cmd:
            yield defer.maybeDeferred(self.connection.write, cmd)
        yield defer.maybeDeferred(self.connection.disconnect)

    @defer.inlineCallbacks
    def submit(self, job, test=False):
        """ Submit the job to the device. If the device is currently running
        a job it will be queued and run when this is finished.

        This handles iteration over the path model defined by the job and
        sending commands to the actual device using roughly the procedure is
        as follows:

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
            test: bool
                Do a test run. This specifies whether the commands should be
                sent to the actual device or not. If True, the connection will
                be replaced with a virtual connection that captures all the
                command output.

        """
        log.debug("device | submit {}".format(job))
        try:

            #: Only allow one job at a time
            if self.busy:
                queue = self.queue[:]
                queue.append(job)
                self.queue = queue  #: Copy and reassign so the UI updates
                log.info("Job {} put in device queue".format(job))
                return

            with self.device_busy():
                #: Set the current the job
                self.job = job
                self.status = "Initializing job"

                #: Get the time to sleep based for each unit of movement
                config = self.config

                #: Rate px/ms
                if config.custom_rate >= 0:
                    rate = config.custom_rate
                elif self.connection.always_spools or config.spooled:
                    rate = 0
                elif config.interpolate:
                    if config.step_time > 0:
                        rate = config.step_size/float(config.step_time)
                    else:
                        rate = 0 # Undefined
                else:
                    rate = from_unit(
                        config.speed,  # in/s or cm/s
                        config.speed_units.split("/")[0])/1000.0

                # Device model is updated in real time
                model = yield defer.maybeDeferred(self.init, job)

                #: Local references are faster
                info = job.info

                #: Determine the length for tracking progress
                whole_path = QtGui.QPainterPath()

                #: Some versions of Qt seem to require a value in
                #: toSubpathPolygons
                m = QtGui.QTransform.fromScale(1, 1)
                for path in model.toSubpathPolygons(m):
                    for i, p in enumerate(path):
                        whole_path.lineTo(p)
                total_length = whole_path.length()
                total_moved = 0
                log.debug("device | Path length: {}".format(total_length))

                #: So a estimate of the duration can be determined
                info.length = total_length
                info.speed = rate*1000  #: Convert to px/s

                #: Waiting for approval
                info.status = 'waiting'

                #: If marked for auto approve start now
                if info.auto_approve:
                    info.status = 'approved'
                else:
                    #: Check for approval before starting
                    yield defer.maybeDeferred(info.request_approval)
                    if info.status != 'approved':
                        self.status = "Job cancelled"
                        return

                #: Update stats
                info.status = 'running'
                info.started = datetime.now()

                self.status = "Connecting to device"
                with self.device_connection(
                                test or config.test_mode) as connection:
                    self.status = "Processing job"
                    try:
                        yield defer.maybeDeferred(self.connect)

                        protocol = connection.protocol

                        #: Write startup command
                        if config.commands_before:
                            yield defer.maybeDeferred(connection.write,
                                                      config.commands_before)

                        self.status = "Working..."

                        if config.force_enabled:
                            yield defer.maybeDeferred(
                                protocol.set_force, config.force)
                        if config.speed_enabled:
                            yield defer.maybeDeferred(
                                protocol.set_velocity, config.speed)

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
                                info.status = 'cancelled'
                                break
                            elif not connection.connected:
                                self.status = "connection error"
                                info.status = 'error'
                                break

                            #: Invoke the command
                            #: If you want to let the device handle more complex
                            #: commands such as curves do it in process and handle
                            yield defer.maybeDeferred(cmd, *args, **kwargs)
                            total_moved += d

                            #: d should be the device must move in px
                            #: so wait a proportional amount of time for the device
                            #: to catch up. This avoids buffer errors from dumping
                            #: everything at once.

                            #: Since sending is way faster than cutting
                            #: we must delay (without blocking the UI) before
                            #: sending the next command or the device's buffer
                            #: quickly gets filled and crappy china piece cutters
                            #: get all jacked up. If the transport sends to a spooled
                            #: output (such as a printer) this can be set to 0
                            if rate > 0:
                                # log.debug("d={}, delay={} t={}".format(
                                #     d, delay, d/delay
                                # ))
                                yield async_sleep(d/rate)

                            #: TODO: Check if we need to update the ui
                            #: Set the job progress based on how far we've gone
                            if total_length > 0:
                                info.progress = int(max(0, min(100,
                                                100*total_moved/total_length)))

                        if info.status != 'error':
                            #: We're done, send any finalization commands
                            yield defer.maybeDeferred(self.finish)

                        #: Write finalize command
                        if config.commands_after:
                            yield defer.maybeDeferred(connection.write,
                                                      config.commands_after)

                        #: Update stats
                        info.ended = datetime.now()

                        #: If not cancelled or errored
                        if info.status == 'running':
                            info.done = True
                            info.status = 'complete'
                    except Exception as e:
                        log.error(traceback.format_exc())
                        raise
                    finally:
                        if connection.connected:
                            yield defer.maybeDeferred(self.disconnect)

            #: Set the origin
            if job.feed_to_end and job.info.status == 'complete':
                self.origin = self.position

            #: If the user didn't cancel, set the origin and
            #: Process any jobs that entered the queue while this was running
            if self.queue and not job.info.cancelled:
                queue = self.queue[:]
                job = queue.pop(0)  #: Pull the first job off the queue
                log.info("Rescheduling {} from queue".format(job))
                self.queue = queue  #: Copy and reassign so the UI updates

                #: Call a minute later
                timed_call(60000, self.submit, job)
        except Exception as e:
            log.error(' device | Execution error {}'.format(
                traceback.format_exc()))
            raise

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

        # Previous point
        _p = QtCore.QPointF(self.origin[0], self.origin[1])

        # Do a final translation since Qt's y axis is reversed from svg's
        # It should now be a bbox of (x=0, y=0, width, height)
        # this creates a copy
        model = model * QtGui.QTransform.fromScale(1, -1)

        # Determine if interpolation should be used
        skip_interpolation = (self.connection.always_spools or config.spooled
                              or not config.interpolate)

        # speed = distance/seconds
        # So distance/speed = seconds to wait
        step_size = config.step_size
        if not skip_interpolation and step_size <= 0:
            raise ValueError("Cannot have a step size <= 0!")
        try:
            # Apply device filters
            for f in self.filters:
                log.debug(" filter | Running {} on model".format(f))
                model = f.apply_to_model(model, job=self)

            # Since Qt's toSubpathPolygons converts curves without accepting
            # a parameter to set the minimum distance between points on the
            # curve, we need to prescale by a "quality factor" before
            # converting then undo the scaling to effectively adjust the
            # number of points on a curve.
            m = QtGui.QTransform.fromScale(
                config.quality_factor, config.quality_factor)
            # Some versions of Qt seem to require a value in toSubpathPolygons
            polypath = model.toSubpathPolygons(m)

            if config.quality_factor != 1:
                # Undo the prescaling, if the quality_factor > 1 the curve
                # quality will be improved.
                m_inv = QtGui.QTransform.fromScale(
                    1/config.quality_factor, 1/config.quality_factor)
                polypath = list(map(m_inv.map, polypath))

            # Apply device filters to polypath
            for f in self.filters:
                log.debug(" filter | Running {} on polypath".format(f))
                polypath = f.apply_to_polypath(polypath)

            for path in polypath:

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

                    #: If the device does not support streaming
                    #: the path interpolation is skipped entirely
                    if skip_interpolation:
                        x, y = p.x(), p.y()
                        yield (l, self.move, ([x, y, z],), {})
                        continue

                    #: Where we are within the subpath
                    d = 0

                    #: Interpolate path in steps of dl and ensure we get
                    #: _p and p (t=0 and t=1)
                    #: This allows us to cancel mid point
                    while d <= l:
                        #: Now set d to the next point by step_size
                        #: if the end of the path is less than the step size
                        #: use the minimum of the two
                        dl = min(l-d, step_size)

                        #: Now find the point at the given step size
                        #: the first point d=0 so t=0, the last point d=l so t=1
                        t = subpath.percentAtLength(d)
                        sp = subpath.pointAtPercent(t)
                        #if d == l:
                        #    break  #: Um don't we want to send the last point??

                        x, y = sp.x(), sp.y()
                        yield (dl, self.move, ([x, y, z],), {})

                        #: When we reached the end but instead of breaking above
                        #: with a d < l we do it here to ensure we get the last
                        #: point
                        if d == l:
                            #: We reached the end
                            break

                        #: Add step size
                        d += dl

            #: Make sure we get the endpoint
            ep = model.currentPosition()
            x, y = ep.x(), ep.y()
            yield (0, self.move, ([x, y, 0],), {})
        except Exception as e:
            log.error("device | processing error: {}".format(
                traceback.format_exc()))
            raise e

    def _observe_status(self, change):
        """ Whenever the status changes, log it """
        log.info("device | {}".format(self.status))

    def _observe_job(self, change):
        """ Save the previous jobs """
        if change['type'] == 'update':
            job = change['value']
            if job not in self.jobs:
                jobs = self.jobs[:]
                jobs.append(job)
                self.jobs = jobs


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

    #: Filters registered in the system
    filters = List(extensions.DeviceFilter)

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
        plugins = []
        with enaml.imports():
            from .transports.raw.manifest import RawFdManifest
            from .transports.serialport.manifest import SerialManifest
            from .transports.printer.manifest import PrinterManifest
            from .transports.disk.manifest import FileManifest
            from .transports.parallelport.manifest import ParallelManifest
            from inkcut.device.protocols.manifest import ProtocolManifest
            from inkcut.device.drivers.manifest import DriversManifest
            from inkcut.device.filters.manifest import FiltersManifest
            from inkcut.device.pi.manifest import PiManifest
            plugins.append(RawFdManifest)
            plugins.append(SerialManifest)
            plugins.append(PrinterManifest)
            plugins.append(FileManifest)
            plugins.append(ParallelManifest)
            plugins.append(ProtocolManifest)
            plugins.append(DriversManifest)
            plugins.append(FiltersManifest)
            plugins.append(PiManifest)

        for Manifest in plugins:
            w.register(Manifest())

        #: This refreshes everything else
        self._refresh_extensions()

        #: Restore state after plugins are loaded
        super(DevicePlugin, self).start()

    def submit(self, job):
        """ Send the given job to the device and restart all stats

        """
        job.info.reset()
        job.info.started = datetime.now()
        return self.device.submit(job)

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
        self.devices = [self.get_device_from_driver(self.drivers[0])]
        return self.devices[0]

    def _observe_device(self, change):
        """ Whenever the device changes, redraw """
        #: Redraw
        plugin = self.workbench.get_plugin('inkcut.job')
        plugin.refresh_preview()

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
        # Set the protocols based on the declaration
        transports = [t for t in self.transports
                      if not driver.connections or t.id == 'disk' or
                      t.id in driver.connections]

        # Set the protocols based on the declaration
        protocols = [p for p in self.protocols
                     if not driver.protocols or p.id in driver.protocols]

        # Generate the device
        return driver.factory(driver, transports, protocols)

    # -------------------------------------------------------------------------
    # Device Extensions API
    # -------------------------------------------------------------------------
    def _refresh_extensions(self):
        """ Refresh all extensions provided by the DevicePlugin """
        self._refresh_protocols()
        self._refresh_transports()
        self._refresh_drivers()
        self._refresh_filters()

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
        drivers.sort(key=lambda d: d.id)

        # Update
        self.drivers = drivers

    def _refresh_filters(self):
        """ Reload all DeviceFilters registered by any Plugins

        Any plugin can add to this list by providing a DeviceFilter
        extension in the PluginManifest.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(extensions.DEVICE_FILTER_POINT)
        filters = []
        for extension in sorted(point.extensions, key=lambda ext: ext.rank):
            for t in extension.get_children(extensions.DeviceFilter):
                filters.append(t)
        self.filters = filters

    # -------------------------------------------------------------------------
    # Live progress API
    # -------------------------------------------------------------------------
    def reset_preview(self):
        """ Clear the preview """
        self._reset_preview(None)

    @observe('device', 'device.job')
    def _reset_preview(self, change):
        """ Redraw the preview on the screen

        """
        view_items = []

        #: Transform used by the view
        preview_plugin = self.workbench.get_plugin('inkcut.preview')
        plot = preview_plugin.live_preview
        t = preview_plugin.transform

        #: Draw the device
        device = self.device
        job = device.job

        r = QtGui.QTransform()
        if device.config.swap_xy:
            # Rotate area to match swapped axis
            r.rotate(90)
            r.scale(-1, 1)

        if device and device.area:
            area = device.area
            view_items.append(
                dict(path=device.transform(device.area.path*t*r),
                     pen=plot.pen_device,
                     skip_autorange=True)
            )

        if job and job.material:
            # Also observe any change to job.media and job.device
            view_items.extend([
                dict(path=device.transform(job.material.path*t*r),
                     pen=plot.pen_media,
                     skip_autorange=True),
                dict(path=device.transform(job.material.padding_path*t*r),
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
