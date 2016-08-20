# -*- coding: utf-8 -*- 
'''
Created on Jan 16, 2015

@author: jrm
'''
import sys
import traceback
from datetime import datetime
from atom.api import observe,Float,Instance,Unicode,Bool,ForwardInstance,ContainerList,Int,Callable
from enaml.core.declarative import Declarative,d_
from enaml.qt import QtCore, QtGui
from inkcut.workbench.core.svg import QtSvgDoc
from inkcut.workbench.core.area import AreaBase
from inkcut.workbench.core.utils import LoggingAtom, async_sleep
from twisted.internet.protocol import Protocol, connectionDone
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor, defer
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol


def deferred_job():
    # Import later to avoid circular import
    from inkcut.workbench.core.job import Job
    return Job

class IDeviceProtocol(LoggingAtom,Protocol):
    """ Basic interface a protocol must implement is to override the 
        move() method. 
    
    Anything you write to the transport should also
    be appended to job.info.data"""
    job = ForwardInstance(deferred_job)
    
    def connectionMade(self):
        pass
    
    def move(self,x,y,z):
        raise NotImplementedError("IDeviceProtocol.move(x,y,z) is not implemented by {}".format(self))
    
    def connectionLost(self, reason=connectionDone):
        Protocol.connectionLost(self, reason=reason)
        
    def write(self,data):
        """ Utility function that writes to the transport
        and appends it to the job's data. """
        self.job.info.data += data
        self.transport.write(data)

class Device(AreaBase):
    """ The role of the device is to serve as a model for the configuration
    of the Plotter/Cutter being used as well as handle the process of actually
    writing do the physical device using whatever protocols and connection it supports."""
    
    # Configuration variables
    name = Unicode('').tag(config=True)
    scale = ContainerList(Float(),default=[1,1]).tag(config=True)
    uses_roll = Bool(False).tag(config=True)
    use_force = Bool(False).tag(config=True)
    use_speed = Bool(False).tag(config=True)
    force = Int(10).tag(config=True)
    speed = Int(20).tag(config=True)
    blade_offset = Float(QtSvgDoc.convertFromUnit(0.25, 'mm')).tag(config=True)
    overcut = Float(QtSvgDoc.convertFromUnit(2, 'mm')).tag(config=True)
    
    # State variables, the UI can watch these
    busy = Bool(False) # Whether the device is currently processing a job
    status = Unicode('')
    position = ContainerList(Float(),default=[0.0,0.0,0.0])
    
    # Driver handles 
    jobs = ContainerList(ForwardInstance(deferred_job))
    
    # Active driver 
    driver = ForwardInstance(lambda:Driver)
    
    def is_supported(self):
        """ Return True if the device is supported. """
        return True
    
    def add_job(self, job):
        """ Cancel a job if it has not already been run. """
        self.jobs.append(job)
    
    def cancel_job(self,job):
        """ Cancel a job if it has not already been run. """
        if job in self.jobs and not job.info.done:
            job.info.cancelled = True
        
    @observe('jobs')
    @inlineCallbacks
    def _process_jobs(self):
        """ Loop that handles any jobs"""
        try:
            for job in self.jobs:
                if not job.info.done and not job.info.cancelled:
                    yield self._process_job(job)
        finally:
            # Run again!
            reactor.callLater(1000,self._process_jobs)
    
    @inlineCallbacks 
    def _process_job(self,job):
        """ Set common properties so the user doesn't have to """
        job.info.started = datetime.now()
        job.info.progress = 0
        self.busy = True
        try:
            yield self.driver.process_job(job)
        except Exception as e:
            job.info.status = str(e)
            self.log.error(traceback.format_exc())
        finally:
            self.busy = False
            job.info.ended = datetime.now()
    

class Driver(LoggingAtom):
    """ A Driver is a class that handles processing a Job"""
    
    @inlineCallbacks
    def process_job(self,job):
        """ Called for each job that is added to the job queue, 
            waiting until the previous job (if any) is finished.        
            
            This should handle the process of reading the path data from the
            job and sending it to the physical device using whatever method needed.
        """
        raise NotImplementedError("Sublcasses must implement this!")
    
    def prepare_job(self,job):
        """ Prepare the paths to be sent to the device apply any device specific transforms here.
        
        If any transforms are done you should make a COPY of the jobs model.
        
        @param model: Instance of Job
        @return: Instance of QPainterPath 
        """
        return job.model
       
class StreamDriver(Driver):
    """ A device that sends data in real time.  It handles the entire process of iterating over 
        the job's path, interpolating it at equal distances and sending each point to the device 
        using the correct protocol.
        
        A stream device can be paused, resumed, and stopped midway. 
    """
    protocol = Instance(IDeviceProtocol)
    
    def process_job(self, job):
        """ Process job using given protocol and iterating over the path."""
        
        protocol = yield defer.maybeDeferred(self.make_connection,job)
        # Should connect immediately
        try:
            model = job.device_model # Device model is updated in real time
            
            x,y,z = self.position # initial state
            
            #speed = self.device.speed # Units/second
            # device.speed is in CM/s
            # d is in PX so...
            # speed = distance/seconds  
            # So distance/speed = seconds to wait
            step_size = 1
            step_time = max(1,round(1000*step_size/QtSvgDoc.parseUnit('%scm'%self.speed)))
            p_len = job.model.length()
            p_moved = 0
            _p = QtCore.QPointF(0,0) # previous point
            dl = step_size
            
            for path in model.toSubpathPolygons():
                for i,p in enumerate(path):
                    subpath = QtGui.QPainterPath()
                    subpath.moveTo(_p)
                    subpath.lineTo(p)
                    l = subpath.length()
                    z = i!=0 and 1 or 0
                    d = 0
                    
                    # Interpolate path in steps of dl and ensure we get _p and p (t=0 and t=1)
                    while d<=l:# and self.isVisible():
                        if job.info.cancelled:
                            return
                        if job.info.paused:
                            yield async_sleep(0.1) # ms
                            continue # Keep waiting...
                            
                        sp = subpath.pointAtPercent(subpath.percentAtLength(d))
                        if d==l:
                            break
                        
                        p_moved+=min(l-d,dl)
                        d = min(l,d+dl)
                    
                        x,y = sp.x(),-sp.y()
                        yield defer.maybeDeferred(protocol.move,x,y,z) 
                        job.info.progress = int(round(100*p_moved/p_len))
                        yield async_sleep(step_time) # ms
                    
                        _p = p
        finally:
            yield defer.maybeDeferred(self.lose_connection,protocol)
            
    def make_connection(self,job):
        """ Called before iterating over the path. Used to make a connection using the device
        and send any initialization commands.
          
        @param job: Instance of Job
        @return: Instance of IDeviceProtocol 
        
        """
        protocol = self.protocol(job)
        return protocol
    
    def lose_connection(self,protocol):
        """ Called after iterating over the path. Used to close the connection or send any finalization commands."""
        pass
    
class SerialDriver(StreamDriver):
    serial_port = ForwardInstance(lambda:SerialPort)
    
    def is_supported(self):
        try:
            global SerialPort
            from twisted.internet.serialport import SerialPort
        except ImportError:
            return False

    def make_connection(self, job):
        protocol = super(SerialDriver, self).make_connection()
        self.serial_port = SerialPort(protocol,self.job.device.port)
        return protocol
    
    def lose_connection(self,protocol):
        if self.serial_port:
            self.serial_port.loseConnection()

class PrinterDriver(StreamDriver):
    """ Device that simply sends the raw data to a system printer device."""
    
    def is_supported(self):
        try:
            if sys.platform=='win32':
                return False
            else:
                global cups
                import cups
                return True
        except ImportError:
            return False
    
    def lose_connection(self,protocol):
        """ When the job is complete, write all the data to the printer device """
        pass

class INetDriver(StreamDriver):
    """ """
    address = Unicode()
    port = Int()
    endpoint = Instance(TCP4ClientEndpoint)
    def make_connection(self, job):
        self.endpoint = TCP4ClientEndpoint(reactor, self.address, self.port)
        protocol = super(INetDriver, self).make_connection(job)
        yield connectProtocol(self.endpoint,protocol)
        #return protocol
    
    def lose_connection(self,protocol):
        protocol.transport.loseConnection()

def generic_factory(driver_def,protocol):
    """ Generate the correct device from the Driver """
    from inkcut.workbench.core import device
    DriverFactory = getattr(device,"{}Driver".format(driver_def.connections[0].title()))
    return DriverFactory(protocol=protocol)
        
class DeviceDriver(Declarative):
    """ Provide meta info about this device """
    # ID of the device
    # If none exits one i created from manufacturer.model
    id = d_(Unicode())
    
    # Name of the device (optional)
    name = d_(Unicode())
    # Model of the device (optional)
    model = d_(Unicode())
    
    # Manufacturer of the device (optional)
    manufacturer = d_(Unicode())
    
    # Width of the device (required)
    width = d_(Unicode())
    
    # Length of the device, if it uses a roll, leave blank
    length = d_(Unicode())
    
    # Step resolution 
    resolution = d_(Unicode())
    
    # Factory to construct the device, 
    # takes a single argument for the protocol
    factory = d_(Callable(default=generic_factory))
    
    # IDs of the protocols supported by this device
    protocols = d_(ContainerList(Unicode()))
    
    # IDs of the transports supported by this device
    connections = d_(ContainerList(Unicode()))  


class DeviceProtocol(Declarative):
    # Id of the protocol
    id = d_(Unicode())
    
    # Name of the protocol (optional)
    name = d_(Unicode())
    
    # Factory to construct the protocol, 
    # takes a single argument for the transport
    factory = d_(Callable())
    
    # Settings to configure the protocol, must return enaml widgets!
    options = d_(Callable())
    
class DeviceTransport(Declarative):
    # Id of the protocol
    id = d_(Unicode())
    
    # Name of the protocol (optional)
    name = d_(Unicode())
    
    # Factory to construct the protocol, 
    # takes a single argument for the transport
    factory = d_(Callable())
    
    # Settings to configure the protocol, must return enaml widgets!
    options = d_(Callable())
    
class DeviceMedia(Declarative):
    # Id of the media
    id = d_(Unicode())
