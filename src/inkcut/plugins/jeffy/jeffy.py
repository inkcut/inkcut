'''
Created on Jan 24, 2015

@author: jrm
'''
import time
import RPi.GPIO as GPIO
from atom.api import Instance,List,Int,Float,Tuple,Dict, Bool
from inkcut.workbench.core.device import Device
from inkcut.workbench.preferences.plugin import Model
from contextlib import contextmanager


class StepperMotor(Model):
    DIR_POS = 1
    DIR_NEG = -1
    
    delay = Float(0.000001)                                 # Default Software Square Wave Time Delay
    driver_pins = Tuple()                                   # StepperMotor Class driver GPIO board pins
    enable_pin = Int()                                      # StepperMotor Class enable GPIO board pins
    enabled = Bool()
    steps = Int(0)                                          # Steps relative to starting position
    
    def __init__(self,*args,**kwargs):
        super(StepperMotor, self).__init__(*args,**kwargs)
        self.init_rpi()
        
    def init_rpi(self):
        pins = list(self.driver_pins) + [self.enable_pin]   # Setup RPi GPIO pins
        GPIO.setup(pins, GPIO.OUT, initial=GPIO.LOW)        # set initial value option (1 or 0)
        
    def _observe_enabled(self,change):                      # Enable motor for duration of this block
        if self.enabled:                                    
            GPIO.output(self.enable_pin, GPIO.HIGH)
        else:
            GPIO.output(self.enable_pin, GPIO.LOW)
    
    def step(self, steps):
        ds = 0 if steps<0 else 1                            # set ds to 0 or 1 for direction pin output
        
        for i in xrange(abs(int(steps))):
                GPIO.output(self.driver_pins, [ds,1])       # Set GPIO output (Direction pin to ds, Pulse Pin High) 
                time.sleep(self.delay)                      # Software Square Wave High Time
                GPIO.output(self.driver_pins, [ds,0])       # Set GPIO output (Direction pin to ds, Pulse Pin Low) 
                time.sleep(self.delay)                      # Software Square Wave Low Time
                  
class JeffyDevice(Device):
    bounds = [[0,0],[0,0]]                                  # End Bounds for Inkcut # TODO: Implement this with actual cutter end bounds        
    motor = Dict(default={})                                # ??? JAIRUS ???
    motor_enable_pins = Tuple(int,default=(3,8))            # (X Driver Enable GPIO Pin, Y Driver Enable GPIO Pin)
    motor_driver_pins = Tuple(tuple,default=(
                        (7, 5),                             # (X Direction Pin, X direction Step Pulse Pin)
                       (12, 10)))                           # (Y Direction Pin, Y direction Step Pulse Pin)
    servo_gpio_pins = Tuple(int,default=(19,17))            # TODO: need to connect these pins to cutter blade outputs
    boundary_gpio_pins = Tuple(int,default=(                # TODO: need to connect these boundary pins to end stop switches
                          (5,6),                            # (-X switch GPIO boundary Pin, +X boundary switch GPIO pin)  #TODO: connect hardware switches to these pins
                          (11,12)))                         # (-Y switch GPIO boundary Pin, +Y boundary switch GPIO pin)  #TODO: connect hardware switches to these pins
    boundary_bounce_timeout = Int(300)                      # Bounce timer for switches [ms] # TODO: integrate timer with end stop switches
    
    scale = Tuple(default=(36.4,36.4))                      # MAGIC VOODOO NUMBER AKA [pixels/motor steps] could also be flipped? not sure  
    delay = Float(0.0035)                                   # Time Delay for Software Implmented Square Wave #TODO: integrate Real-Time Clock to replace software square wave

    _position = List(default=[0,0])
    
    def _default_step_time(self):
        return 0.0

    def _default_step_size(self):
        return self.scale[0]
    
    def connect(self):
        self.log.info("Jeffy Device connected boss")
        self.init_rpi()
        self.init_motors()
        self.connectionMade()

    def disconnect(self):
        self.motor[0].enabled = False
        self.motor[1].enabled = False
    
    def init(self, job):        

        #: Do QRCode stuff
        #rotation,x,y = QRcodeWork.register()

        #job.rotation = rotation
        # Left, Top, Right, Bottom#job.
        #job.media.padding = [x, y, 0, 0]

        self._position = [0,0] # Clear                    #: Updating this does not update the UI

        return job.model

        
    def init_rpi(self):
        GPIO.setmode(GPIO.BOARD)
    
    def init_motors(self):
        """ Creates motor instances and sets the output pins """
            
        # Init motors
        self.motor[0] = StepperMotor(driver_pins=self.motor_driver_pins[0],enable_pin=self.motor_enable_pins[0])
        self.motor[1] = StepperMotor(driver_pins=self.motor_driver_pins[1],enable_pin=self.motor_enable_pins[1])

        self.motor[0].enabled = True
        self.motor[1].enabled = True
        
        
    def init_boundary_sensors(self,pins=None):
        if pins is not None:
            self.boundary_gpio_pins = pins
        
        if self.skip_gpio:
            return
#          
#         # Init boundary pins
#         RPIO.setup(self.boundary_gpio_pins[0][0], RPIO.IN, pull_up_down = RPIO.PUD_UP)
#         RPIO.setup(self.boundary_gpio_pins[0][1], RPIO.IN, pull_up_down = RPIO.PUD_UP)
#         RPIO.setup(self.boundary_gpio_pins[1][0], RPIO.IN, pull_up_down = RPIO.PUD_UP)
#         RPIO.setup(self.boundary_gpio_pins[1][1], RPIO.IN, pull_up_down = RPIO.PUD_UP)
#          
#         # Init callbacks
#         RPIO.add_interrupt_callback(self.boundary_gpio_pins[0][0], callback=self.on_hit_bound_min_x, debounce_timeout_ms=self.boundary_bounce_timeout)
#         RPIO.add_interrupt_callback(self.boundary_gpio_pins[0][1], callback=self.on_hit_bound_max_x, debounce_timeout_ms=self.boundary_bounce_timeout)
#         RPIO.add_interrupt_callback(self.boundary_gpio_pins[1][0], callback=self.on_hit_bound_min_y, debounce_timeout_ms=self.boundary_bounce_timeout)
#         RPIO.add_interrupt_callback(self.boundary_gpio_pins[1][1], callback=self.on_hit_bound_max_y, debounce_timeout_ms=self.boundary_bounce_timeout)
        
    def reset(self):
        """ Checks the boundaries and then moves to the (0,0) position. """
        self.check_bounds()
        self.move(0,0,absolute=True)
    
    def move(self,dx,dy,z,absolute=False):
        """ Move to position. Based on http://goldberg.berkeley.edu/pubs/XY-Interpolation-Algorithms.pdf
         
        @param: dx, steps in x direction or x position
        @param: dy, steps in y direction or y position
        @param: callback, called for each step moved
        @param: absolute, if true move to absolute position, else move relative to current position
        """
        #self.log.debug("Move: to ({},{},{}) from ({}) (abs {})".format(dx,dy,z,self.position, absolute))
        dx,dy = int(dx*self.scale[0]), int(dy*self.scale[1])
              
        if absolute:
            #raise NotImplementedError
            dx -= self._position[0]
            dy -= self._position[1]

        if dx==dy==0:
            return
        
        sx = dx>0 and 1 or -1
        sy = dy>0 and 1 or -1
        epsilon = 0.000001
        
        fxy = abs(dx)-abs(dy)
        #if fxy==0:
        #    return self.position
        x,y = 0,0
        try:
            while True:
                if fxy<0:
                    mx,my = 0,sy
                    fxy += abs(dx)
                else:
                    mx,my = sx,0
                    fxy -= abs(dy)
                
                self.motor[0].step(mx)
                self.motor[1].step(my)
          
                x += mx
                y += my
                
                self._position = [(self._position[0]+mx),(self._position[1]+my),self.position[2]]
                #self.log.debug("x={} dx={}, y={} dy={}".format(x,dx,y,dy))
                if x==dx and y==dy:
                    break
                
        except KeyboardInterrupt:
             self.disconnect()
             raise
        #self.position = [dx, dy, z]        # Udpate for Inkcut Real-Time Update
        #return self.position               # Update for Inkcut Real-Time Update
    
    def set_velocity(self, v):                           # TODO: Map v to delay
        Device.set_velocity(self, v)
    
    def check_bounds(self):                              # TODO: Develop cutter range check with end stop switches       
        for i in xrange(self.MAX_X):                     # Move -x until we hit min x bound pin
            self.move(-1,0)
        for i in xrange(self.MAX_Y):                     # Move -y until we hit min y bound pin
            self.move(0,-1)
            # Move +x until we hit max x bound pin
            # Move +y until we hit max y bound pin
        pass
    
    def on_hit_bound_min_x(self):
        self.position[0] = 0
    
    def on_hit_bound_max_x(self):
        self.position[0] = self.MAX_X
    
    def on_hit_bound_min_y(self):
        self.position[1] = 0
    
    def on_hit_bound_max_y(self):
        self.position[1] = self.MAX_Y
        

# class JeffyProtocol(IDeviceProtocol):
#     """ Hooks into UI """ 
#     plotter = Instance(Plotter2D)
#     def init(self):
#         self.plotter = Plotter2D()
#         
#     def move(self, x, y, z):
#         self.plotter.move(x, y,absolute=True)
#     
        

