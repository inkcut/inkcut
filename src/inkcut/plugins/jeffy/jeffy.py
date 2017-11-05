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
    
    delay = Float(0.000001) # time in seconds to hold the output at the set value
    driver_pins = Tuple()
    enable_pin = Int()
    enabled = Bool()
    steps = Int(0) # Steps relative to starting position
    
    #_cur_step = Int(0) # Index of step sequence array
    #step_sequence = List(default=[(1,0,1,0),
    #                 (0,0,1,0),
    #                 (0,1,1,0),
    #                 (0,1,0,0),
    #                 (0,1,0,1),
    #                 (0,0,0,1),
    #                 (1,0,0,1),
    #                 (1,0,0,0)]) # output values for half stepping
        
    def __init__(self,*args,**kwargs):
        super(StepperMotor, self).__init__(*args,**kwargs)
        self.init_rpi()
        
    def init_rpi(self):
        # Init pins
        pins = list(self.driver_pins) + [self.enable_pin]
        GPIO.setup(pins, GPIO.OUT, initial=GPIO.LOW)    # set initial value option (1 or 0)
        
    
    def _observe_enabled(self,change):
        """ Enable motor for duration of this block """
        if self.enabled:
            GPIO.output(self.enable_pin, GPIO.HIGH)
        else:
            GPIO.output(self.enable_pin, GPIO.LOW)
    
    def step(self, steps):
        ds = 0 if steps<0 else 1#self.DIR_NEG or self.DIR_POS
        #with self.enabled():
        #print(self,steps)
        for i in xrange(abs(int(steps))):
                GPIO.output(self.driver_pins, [ds,1])     # set an output port/pin value to 1/GPIO.HIGH/True
                time.sleep(self.delay)
                GPIO.output(self.driver_pins, [ds,0])     # set an output port/pin value to 1/GPIO.HIGH/True
                time.sleep(self.delay)


            
##    def step_legacy(self,steps):
##        """ Step the motor steps times. Direction depends on sign of steps.
##        
##        @param steps: number of steps to take
##        @yields delay: how long to wait before continuing
##        """
##        ds = steps<0 and self.DIR_NEG or self.DIR_POS
##        
##        for i in xrange(abs(steps)):
##            self._cur_step = (self._cur_step + ds) % len(self.step_sequence)
##            output = self.step_sequence[self._cur_step]
##            self._set_output(output)
##            self.steps +=ds # Update total step count
##            yield self.delay
##            #if self.delay>0:
##            #    time.sleep(self.delay) 
            
    def _set_output(self,output):
        """ You should not use this directly! 
        Sets the output pins to the given value.
        
        Example:
            pins = [1,2,3,4]
            value = 8 --> 0b1000
            
            will set pins to following outputs:
            pin:    1    2    3    4
            lvl:    1    0    0    0
            
            value = 5 --> 0b0101
            
            will set pins to following outputs:
            pin:    1    2    3    4
            lvl:    0    1    0    1
        
        
        """
        GPIO.output(self.driver_pins, output)     # set an output port/pin value to 1/GPIO.HIGH/True
        
            
class JeffyDevice(Device):
    bounds = [[0,0],[0,0]]
    motor = Dict(default={})
    motor_enable_pins = Tuple(int,default=(3,8))
    motor_driver_pins = Tuple(tuple,default=(
                        (7, 5),              ## [X Direction Pin, X direction Step Pulse Pin]
                       (12, 10)))            ## [Y Direction Pin, Y direction Step Pulse Pin]
    servo_gpio_pins = Tuple(int,default=(19,17))    ## Probably blade up and down
    boundary_gpio_pins = Tuple(int,default=(        ## Boundary switch input pins
                          (5,6),
                          (11,12)))
    boundary_bounce_timeout = Int(300) # ms         ## Bounce timer for switches
    
    
    scale = Tuple(default=(36.4,36.4))            # DO NOT LOSE THE MAGIC NUMBER
    delay = Float(0.0035)

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

        #: Updating this does not update the UI
        self._position = [0,0] # Clear

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
        #scale = 1021/90.0
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
                
                # TODO: Interleave steps to make it smoother??
                # TODO: Set position on each step
                self.motor[0].step(mx)
                #for delay in self.motor[0].step(mx):
                #    if delay:
                #        time.sleep(delay)
                self.motor[1].step(my)
                #for delay in self.motor[1].step(my):
                #    if delay:
                #        time.sleep(delay)
                
                x += mx
                y += my
                
                # Update position 
                self._position = [(self._position[0]+mx),(self._position[1]+my),self.position[2]]
                #self.log.debug("x={} dx={}, y={} dy={}".format(x,dx,y,dy))
                if x==dx and y==dy: #abs(x-dx) < epsilon and abs(y-dy) < epsilon:
                    break
                
                #time.sleep(self.delay)
        except KeyboardInterrupt:
             self.disconnect()
             raise
        #self.position = [dx, dy, z]
        
        #return self.position
    
    def set_velocity(self, v):
        # TODO: Map v to delay
        Device.set_velocity(self, v)
    
    def check_bounds(self):
        # Move -x until we hit min x bound pin
        for i in xrange(self.MAX_X):
            self.move(-1,0)
        
        # Move -y until we hit min y bound pin
        for i in xrange(self.MAX_Y):
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
        

