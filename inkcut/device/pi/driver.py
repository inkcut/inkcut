"""
Copyright (c) 2017, Vinylmark LLC.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jan 24, 2015

@author: jrm
@author: jjm
"""
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


class StepperMotor(Model):
    DIR_POS = 1
    DIR_NEG = -1

    # Default Software Square Wave Time Delay (in ms)
    delay = Float(0.001)

    # StepperMotor Class driver GPIO board pins
    driver_pins = Tuple()

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

    @inlineCallbacks
    def step(self, steps):
        # set ds to 0 or 1 for direction pin output
        ds = 0 if steps < 0 else 1
        
        for i in range(abs(int(steps))):

            # Set GPIO output (Direction pin to ds, Pulse Pin High)
            GPIO.output(self.driver_pins, [ds, 1])

            # Software Square Wave High Time
            yield async_sleep(self.delay)

            # Set GPIO output (Direction pin to ds, Pulse Pin Low)
            GPIO.output(self.driver_pins, [ds, 0])

            # Software Square Wave Low Time
            yield async_sleep(self.delay)
                  

class PiConfig(DeviceConfig):

    #: Enable crop code registration
    crop_mark_registration = Bool().tag(config=True)

    # End Bounds for Inkcut
    # TODO: Implement this with actual cutter end bounds
    bounds = Tuple(default=[[0, 0], [0, 0]]).tag(config=True)

    # (X Driver Enable GPIO Pin, Y Driver Enable GPIO Pin)
    motor_enable_pins = Tuple(int, default=(3, 8)).tag(config=True)

    motor_driver_pins = Tuple(tuple, default=(
        (7, 5),   # (X Direction Pin, X direction Step Pulse Pin)
        (12, 10)) # (Y Direction Pin, Y direction Step Pulse Pin)
    ).tag(config=True)

    # TODO: need to connect these pins to cutter blade outputs
    servo_gpio_pins = Tuple(int, default=(19, 17)).tag(config=True)

    # TODO: need to connect these boundary pins to end stop switches
    # TODO: connect hardware switches to these pins
    boundary_gpio_pins = Tuple(tuple, default=(
        (5, 6),  # (-X switch GPIO boundary Pin, +X boundary switch pin)
        (11, 12)) # (-Y switch GPIO boundary Pin, +Y boundary switch pin)
    ).tag(config=True)

    # Bounce timer for switches [ms]
    # TODO: integrate timer with end stop switches
    boundary_bounce_timeout = Int(300).tag(config=True)

    # MAGIC VOODOO NUMBER AKA [pixels/motor steps] could also be flipped?
    # not sure
    scale = Tuple(float, default=(36.4, 36.4)).tag(config=True)

    # Time Delay for Software Implemented Square Wave in ms
    # TODO: integrate Real-Time Clock to replace software square wave
    delay = Float(3.5).tag(config=True)

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
    _position = List(int, default=[0, 0])
    
    def connect(self):
        log.info("Device connected")
        self.init_rpi()
        self.init_motors()

    def disconnect(self):
        """ Set the motors to disabled """
        for motor in self.motor.values():
            motor.enabled = False

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
        config = self.config
        # Init motors
        self.motor[0] = StepperMotor(driver_pins=config.motor_driver_pins[0],
                                     enable_pin=config.motor_enable_pins[0])
        self.motor[1] = StepperMotor(driver_pins=config.motor_driver_pins[1],
                                     enable_pin=config.motor_enable_pins[1])

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

    @inlineCallbacks
    def move(self, dx, dy, z, absolute=False):
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
        #log.debug("Move: to ({},{},{}) 
        # from ({}) (abs {})".format(dx,dy,z,self.position, absolute))
        config = self.config
        dx, dy = int(dx*config.scale[0]), int(dy*config.scale[1])
              
        if absolute:
            dx -= self._position[0]
            dy -= self._position[1]

        if dx == dy == 0:
            return
        
        sx = dx > 0 and 1 or -1
        sy = dy > 0 and 1 or -1

        fxy = abs(dx)-abs(dy)
        x, y = 0, 0
        try:
            while True:
                if fxy < 0:
                    mx, my = 0, sy
                    fxy += abs(dx)
                else:
                    mx, my = sx, 0
                    fxy -= abs(dy)

                #: Wait for both movements to complete
                yield DeferredList(self.motor[0].step(mx),
                                   self.motor[1].step(my))

                x += mx
                y += my
                
                self._position = [self._position[0]+mx,
                                  self._position[1]+my,
                                  self.position[2]]
                #  log.debug("x={} dx={}, y={} dy={}".format(x,dx,y,dy))
                if x == dx and y == dy:
                    break
                
        except KeyboardInterrupt:
            self.disconnect()
            raise

        # Update for Inkcut Real-Time Update
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
