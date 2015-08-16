'''
Created on Jan 24, 2015

@author: jrm
'''
import time
import RPi.GPIO as GPIO
from atom.api import Instance,List,Int,Float,Tuple,Dict
from inkcut.workbench.core.device import Device
from inkcut.workbench.core.utils import ConfigurableAtom

class StepperMotor(ConfigurableAtom):
    DIR_POS = 1
    DIR_NEG = -1
    
    delay = Float(0) # time in seconds to hold the output at the set value
    driver_pins = Tuple()
    enable_pin = Tuple()
    _cur_step = Int(0) # Index of step sequence array
    steps = Int(0) # Steps relative to starting position
    step_sequence = List(default=[(1,0,1,0),
                     (0,0,1,0),
                     (0,1,1,0),
                     (0,1,0,0),
                     (0,1,0,1),
                     (0,0,0,1),
                     (1,0,0,1),
                     (1,0,0,0)]) # output values for half stepping
        
    def __init__(self,*args,**kwargs):
        super(StepperMotor, self).__init__(*args,**kwargs)
        self.init_rpi()
        
    def init_rpi(self):
        # Init pins
        GPIO.setup(self.pins, GPIO.OUT, initial=GPIO.LOW)    # set initial value option (1 or 0)
        
            
    def step(self,steps):
        """ Step the motor steps times. Direction depends on sign of steps.
        
        @param steps: number of steps to take
        @yields delay: how long to wait before continuing
        """
        ds = steps<0 and self.DIR_NEG or self.DIR_POS
        
        for i in xrange(abs(steps)):
            self._cur_step = (self._cur_step + ds) % len(self.step_sequence)
            output = self.step_sequence[self._cur_step]
            self._set_output(output)
            self.steps +=ds # Update total step count
            yield self.delay
            #if self.delay>0:
            #    time.sleep(self.delay) 
            
    def _set_output(self,output):
        """ You should not use this directly! Sets the output pins to the given value.
        
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
    motor = Dict(Int(),Instance(StepperMotor),default={})
    motor_enable_pins = Tuple(Int(),default=(13,15))
    motor_driver_pins = Tuple(Int(),default=(
                        (3,5,7,11),
                       (8,10,12,16)))
    servo_gpio_pins = Tuple(Int(),default=(19,17))
    boundary_gpio_pins = Tuple(Int(),default=(
                          (5,6),
                          (11,12)))
    boundary_bounce_timeout = Int(300) # ms
    
    
    scale = Tuple(default_value=(1,1)) # TODO: This is not used
    delay = Float(0.0035)
    
    def init(self):        
        self.init_rpi()
        self.init_motors()
    
    def init_rpi(self):
        GPIO.setmode(GPIO.BOARD)
    
    def init_motors(self):
        """ Creates motor instances and sets the output pins """
            
        # Init motors
        self.motor[0] = StepperMotor(driver_pins=self.motor_driver_pins[0],enable_pin=self.motor_enable_pins[0])
        self.motor[1] = StepperMotor(driver_pins=self.motor_driver_pins[1],enable_pin=self.motor_enable_pins[1])
        
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

    def close(self):
        self.set_motors_enabled(False) # Disable
        
    def set_motors_enabled(self,enabled):
        pass

        
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
        if absolute:
            dx -= self.position[0]
            dy -= self.position[1]
        
        sx = dx>0 and 1 or -1
        sy = dy>0 and 1 or -1
        
        fxy = abs(dx)-abs(dy)
        x,y = 0,0
        
        while True:
            if fxy<0:
                mx,my = 0,sy
                fxy += abs(dx)
            else:
                mx,my = sx,0
                fxy -= abs(dy)
            
            # TODO: Interleave steps to make it smoother??
            # TODO: Set position on each step
            for delay in self.motor[0].step(mx):
                if delay:
                    time.sleep(delay)
            for delay in self.motor[1].step(my):
                if delay:
                    time.sleep(delay)
            
            x += mx
            y += my
            
            # Update position 
            self.position = (self.position[0]+mx,self.position[1]+my,self.position[2])
                
            if x==dx and y==dy:
                break
            
            time.sleep(self.delay)
 
        return self.position
    
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
        

