"""
Copyright (c) 2017, Vinylmark LLC.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jan 24, 2015

@author: jrm
@author: jjm
"""
import time
import pstats
from cProfile import Profile
from atom.api import Instance, List, Int, Float, Tuple, Dict, Bool, observe
from inkcut.core.api import Model
from inkcut.core.utils import async_sleep, log
from inkcut.device.plugin import Device, DeviceConfig
from twisted.internet.defer import inlineCallbacks, DeferredList
from contextlib import contextmanager
from enaml.qt import QtGui
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

try:
    #: Moved here so I can still test it on the desktop
    from . import registration
    CM_AVAILABLE = True
except ImportError:
    registration = None
    CM_AVAILABLE = False

PROFILER = Profile()


class StepperMotor(Model):
    DIR_POS = 1
    DIR_NEG = -1

    # Default Software Square Wave Time Delay (in ms)
    delay = Float(3.5)
    Clock_Time=Float(time.time())         # Initializate Step_Time

    # StepperMotor Class driver GPIO board pins
    driver_pins = List()

    # StepperMotor Class enable GPIO board pins
    enable_pin = Int()

    enabled = Bool()

    # Steps relative to starting position
    steps = Int(0)
    
    def __init__(self, *args, **kwargs):
        super(StepperMotor, self).__init__(*args, **kwargs)
        if not GPIO_AVAILABLE:
            return
        self.init_rpi()
        
    def init_rpi(self):
        # Setup RPi GPIO pins
        pins = list(self.driver_pins) + [self.enable_pin]

        # set initial value option (1 or 0)
        GPIO.setup(pins, GPIO.OUT, initial=GPIO.LOW)
        
    def _observe_enabled(self, change):
        if not GPIO_AVAILABLE:
            return

        if self.enabled:
            GPIO.output(self.enable_pin, GPIO.HIGH)
        else:
            GPIO.output(self.enable_pin, GPIO.LOW)

    @contextmanager
    def power_enabled(self):
        """ Enable motors for duration of this block """
        self.enabled = True
        try:
            yield
        finally:
            self.enabled = False

    #@inlineCallbacks
    def step(self, steps):
        # set ds to 0 or 1 for direction pin output
        ds = 0 if steps < 0 else 1
        n = int(abs(steps))
        pins = self.driver_pins
        output = GPIO.output
        i = 0
        while i < n:
            while time.time()<(self.Clock_Time+(self.delay/1000000.0)):
                if 0:            # Do nothing # This is effectively time.sleep() however the sleep time is adjusted based on how long it takes to execute other sections of code
                    time.time()
            
            self.Clock_Time = time.time()                   # Set previous clock time to current time

            # Set GPIO output (Direction pin to ds, Pulse Pin High)
            output(pins, (ds, 1))

            # Software Square Wave High Time
            time.sleep(0.000003)                            # DRV8825 requires a minium high pulse of 2us making 3us for margin

            # Set GPIO output (Direction pin to ds, Pulse Pin Low)
            output(pins, (ds, 0))

            i+=1
                  

class PiConfig(DeviceConfig):

    #: Enable crop code registration
    crop_mark_registration = Bool().tag(config=True)

    # End Bounds for Inkcut
    # TODO: Implement this with actual cutter end bounds
    bounds = List(default=[[0, 0], [0, 0]]).tag(config=True)

    # (X Driver Enable GPIO Pin, Y Driver Enable GPIO Pin)
    motor_enable_pins = List(int, default=[3, 8]).tag(config=True)

    motor_driver_pins = List(list, default=[
        [7, 5],   # (X Direction Pin, X direction Step Pulse Pin)
        [12, 10] # (Y Direction Pin, Y direction Step Pulse Pin)
    ]).tag(config=True)

    # TODO: need to connect these pins to cutter blade outputs
    servo_gpio_pins = List(int, default=[19, 17]).tag(config=True)

    # TODO: need to connect these boundary pins to end stop switches
    # TODO: connect hardware switches to these pins
    boundary_gpio_pins = List(list, default=[
        [5, 6],  # (-X switch GPIO boundary Pin, +X boundary switch pin)
        [11, 12] # (-Y switch GPIO boundary Pin, +Y boundary switch pin)
    ]).tag(config=True)

    # Bounce timer for switches [ms]
    # TODO: integrate timer with end stop switches
    boundary_bounce_timeout = Int(300).tag(config=True)

    # MAGIC VOODOO NUMBER AKA [pixels/motor steps] could also be flipped?
    # not sure
    scale = List(float, default=[36.4, 36.4]).tag(config=True)

    # Time Delay for Software Implemented Square Wave in ms
    # TODO: integrate Real-Time Clock to replace software square wave
    delay = Float(3.5).tag(config=True)

    def _default_custom_rate(self):
        return 0

    def _default_step_time(self):
        return 0.0    

    def _default_step_size(self):
        return self.scale[0]


class PiDevice(Device):
    #: Mapping of stepper motor axis to StepperMotor instance
    motor = Dict()

    #: Config that is editable by Inkcut
    config = Instance(PiConfig, ())

    #: Internal position
    _position = List(int, default=[0, 0, 0])

    #: Last update time
    _updated = Float()
    
    def connect(self):
        self.init_rpi()
        self.init_motors({'type':'manual'})
        for motor in self.motor.values():
            motor.enabled = True
        self.connection.connected = True
        log.info("Pi mmotors enabled")
        PROFILER.enable()

    def disconnect(self):
        """ Set the motors to disabled """
        for motor in self.motor.values():
            motor.enabled = False
        self.connection.connected = False
        log.info("Pi mmotors disabled")

        #: Debugging...
        PROFILER.disable()
        stats = pstats.Stats(PROFILER)
        stats.sort_stats('tottime')
        stats.print_stats()

    def init(self, job):
        if not CM_AVAILABLE:
            return job.model

        #: Do crop mark registration
        x, y, rotation = registration.process(job)
        t = QtGui.QTransform()
        t.rotate(rotation)
        t.translate(x, y)

        #: Create the transformed model
        model = job.model * t

        # Clear
        #: Updating this does not update the UI
        self._position = [0, 0]

        return model

    def init_rpi(self):
        """ """
        if not GPIO_AVAILABLE:
            return
        GPIO.setmode(GPIO.BOARD)

    @observe('config', 'config.motor_driver_pins', 'config.motor_enable_pins')
    def init_motors(self, change):
        """ Creates motor instances and sets the output pins """
        if change['type'] == 'create':
            return
        config = self.config
        # Init motors
        self.motor[0] = StepperMotor(driver_pins=config.motor_driver_pins[0],
                                     enable_pin=config.motor_enable_pins[0],
                                     delay=config.delay)
        self.motor[1] = StepperMotor(driver_pins=config.motor_driver_pins[1],
                                     enable_pin=config.motor_enable_pins[1],
                                     delay=config.delay)
        

    def enable(self):
        """ Set the motors to disabled """
        for motor in self.motor.values():
            motor.enabled = True

    def init_boundary_sensors(self, pins=None):
        if pins is not None:
            self.config.boundary_gpio_pins = pins

        # Init boundary pins
        for i in range(2):
            GPIO.setup(self.boundary_gpio_pins[i][0], GPIO.IN,
                       pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.boundary_gpio_pins[i][1], GPIO.IN,
                       pull_up_down=GPIO.PUD_UP)

        # Init callbacks
        bbt = self.boundary_bounce_timeout
        GPIO.add_interrupt_callback(self.boundary_gpio_pins[0][0],
                                    callback=self.on_hit_bound_min_x,
                                    debounce_timeout_ms=bbt)
        GPIO.add_interrupt_callback(self.boundary_gpio_pins[0][1],
                                    callback=self.on_hit_bound_max_x,
                                    debounce_timeout_ms=bbt)
        GPIO.add_interrupt_callback(self.boundary_gpio_pins[1][0],
                                    callback=self.on_hit_bound_min_y,
                                    debounce_timeout_ms=bbt)
        GPIO.add_interrupt_callback(self.boundary_gpio_pins[1][1],
                                    callback=self.on_hit_bound_max_y,
                                    debounce_timeout_ms=bbt)

    @inlineCallbacks
    def reset(self):
        """ Checks the boundaries and then moves to the (0,0) position. """
        yield self.check_bounds()
        yield self.move(0, 0, absolute=True)

    #@inlineCallbacks
    def move(self, position, absolute=True):
        """ Move to position. Based on this publication
        http://goldberg.berkeley.edu/pubs/XY-Interpolation-Algorithms.pdf
         
        Parameters
        ----------
            dx: int
                steps in x direction or x position
            dy: int
                steps in y direction or y position
            absolute: boolean
                if true move to absolute position, else move relative to 
                current position
        
        """
        dx, dy, z = position
        #: Local refs are faster
        config = self.config
        dx, dy = int(dx*config.scale[0]), int(dy*config.scale[1])
        _pos = self._position

        if absolute:
            dx -= _pos[0]
            dy -= _pos[1]

        if dx == dy == 0:
            log.info("{}, {}".format(_pos, _pos))
            return

        sx = dx > 0 and 1 or -1
        sy = dy > 0 and 1 or -1
        fxy = abs(dx)-abs(dy)
        x, y = 0, 0
        ax, ay = abs(dx), abs(dy)
        stepx, stepy = self.motor[0].step, self.motor[1].step
        log.info("{}, {}".format(dx, dy))
        try:
            while True:
                if fxy < 0:
                    fxy += ax
                    stepy(sy)
                    y += sy
                else:
                    fxy -= ay
                    stepx(sx)
                    x += sx

                #: Wait for both movements to complete
                #yield DeferredList([stepx(mx),
                #                    stepy(my)])

                #  log.debug("x={} dx={}, y={} dy={}".format(x,dx,y,dy))
                if x == dx and y == dy:
                    self._position = [_pos[0]+dx, _pos[1]+dy, z]
                    break
                
        except KeyboardInterrupt:
            self.disconnect()
            raise
        log.debug(self._position)
        self.position = position
        # Update for Inkcut Real-Time Update
        #t = time.time()
        #if t-self._updated > 1:
        #    self._updated = t
        #    #: The control panel uses relative
        #    #: so always update
        #    self.position = position
        #else:
        # TODO: Update every so often    
        # self.position = [dx, dy, z]
        # return self.position

    @inlineCallbacks
    def check_bounds(self):
        """ Do a cutter range check with end stop switches 
        """

        # Move -x until we hit min x bound pin
        for i in range(self.MAX_X):
            yield self.move(-1, 0)

        # Move -y until we hit min y bound pin
        for i in range(self.MAX_Y):
            yield self.move(0, -1)
            # Move +x until we hit max x bound pin
            # Move +y until we hit max y bound pin

    def on_hit_bound_min_x(self):
        self.position[0] = 0
    
    def on_hit_bound_max_x(self):
        self.position[0] = self.MAX_X
    
    def on_hit_bound_min_y(self):
        self.position[1] = 0
    
    def on_hit_bound_max_y(self):
        self.position[1] = self.MAX_Y
