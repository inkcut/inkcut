"""
Copyright (c) 2017, Vinylmark LLC.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jan 24, 2015

@author: jrm
@author: jjm
"""
import time
from atom.api import Instance, List, Int, Float, Tuple, Dict, Bool, observe
from inkcut.core.api import Model
from inkcut.device.plugin import Device, DeviceConfig

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

try:
    #: Moved here so I can still test out crap
    from PIL import Image
    from matplotlib import pyplot as plt
    import cv2
    import zbar
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


class StepperMotor(Model):
    DIR_POS = 1
    DIR_NEG = -1
                                                            # Test Git Commit
    delay = Float(0.000001)                                 # Default Software Square Wave Time Delay
    driver_pins = Tuple()                                   # StepperMotor Class driver GPIO board pins
    enable_pin = Int()                                      # StepperMotor Class enable GPIO board pins
    enabled = Bool()
    steps = Int(0)                                          # Steps relative to starting position
    
    def __init__(self, *args, **kwargs):
        super(StepperMotor, self).__init__(*args, **kwargs)
        if not GPIO_AVAILABLE:
            return
        self.init_rpi()
        
    def init_rpi(self):
        pins = list(self.driver_pins) + [self.enable_pin]   # Setup RPi GPIO pins
        GPIO.setup(pins, GPIO.OUT, initial=GPIO.LOW)        # set initial value option (1 or 0)
        
    def _observe_enabled(self, change):                      # Enable motor for duration of this block
        if not GPIO_AVAILABLE:
            return
        if self.enabled:
            GPIO.output(self.enable_pin, GPIO.HIGH)
        else:
            GPIO.output(self.enable_pin, GPIO.LOW)
    
    def step(self, steps):
        ds = 0 if steps < 0 else 1                            # set ds to 0 or 1 for direction pin output
        
        for i in range(abs(int(steps))):
                GPIO.output(self.driver_pins, [ds, 1])       # Set GPIO output (Direction pin to ds, Pulse Pin High)
                time.sleep(self.delay)                      # Software Square Wave High Time
                GPIO.output(self.driver_pins, [ds, 0])       # Set GPIO output (Direction pin to ds, Pulse Pin Low)
                time.sleep(self.delay)                      # Software Square Wave Low Time
                  

class PiConfig(DeviceConfig):

    #: Enable qr code registration
    crop_mark_registration = Bool()

    # End Bounds for Inkcut
    # TODO: Implement this with actual cutter end bounds
    bounds = Tuple(default=[[0, 0], [0, 0]])

    # (X Driver Enable GPIO Pin, Y Driver Enable GPIO Pin)
    motor_enable_pins = Tuple(int, default=(3, 8))

    motor_driver_pins = Tuple(tuple, default=(
        (7, 5),     # (X Direction Pin, X direction Step Pulse Pin)
        (12, 10)))  # (Y Direction Pin, Y direction Step Pulse Pin)

    # TODO: need to connect these pins to cutter blade outputs
    servo_gpio_pins = Tuple(int, default=(19, 17))

    # TODO: need to connect these boundary pins to end stop switches
    # TODO: connect hardware switches to these pins
    boundary_gpio_pins = Tuple(tuple, default=(
        (5, 6),  # (-X switch GPIO boundary Pin, +X boundary switch pin)
        (11, 12))) # (-Y switch GPIO boundary Pin, +Y boundary switch pin)

    # Bounce timer for switches [ms]
    # TODO: integrate timer with end stop switches
    boundary_bounce_timeout = Int(300)

    # MAGIC VOODOO NUMBER AKA [pixels/motor steps] could also be flipped?
    # not sure
    scale = Tuple(float, default=(36.4, 36.4))

    # Time Delay for Software Implemented Square Wave
    # TODO: integrate Real-Time Clock to replace software square wave
    delay = Float(0.0035)

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
        self.log.info("Jeffy Device connected boss")
        self.init_rpi()
        self.init_motors()
        self.connectionMade()

    def disconnect(self):
        """ Set the motors to disabled """
        for motor in self.motor.values():
            motor.enabled = False

    def init(self, job):        
        x, y, rotation = self.QR_Registration()
        job.rotation = rotation

        # Left, Top, Right, Bottom#job.
        # TODO: Will not work. Translation is not the same as padding
        job.media.padding = [x, y, 0, 0]

        # Clear
        #: Updating this does not update the UI
        self._position = [0, 0]

        return job.model

    def init_rpi(self):
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
        self.move(0, 0, absolute=True)
    
    def move(self, dx, dy, z, absolute=False):
        """ Move to position. 
        Based on http://goldberg.berkeley.edu/pubs/
                                            XY-Interpolation-Algorithms.pdf
         
        @param: dx, steps in x direction or x position
        @param: dy, steps in y direction or y position
        @param: callback, called for each step moved
        @param: absolute, if true move to absolute position, else move relative to current position
        """
        #self.log.debug("Move: to ({},{},{}) from ({}) (abs {})".format(dx,dy,z,self.position, absolute))
        config = self.config
        dx, dy = int(dx*config.scale[0]), int(dy*config.scale[1])
              
        if absolute:
            #raise NotImplementedError
            dx -= self._position[0]
            dy -= self._position[1]

        if dx == dy == 0:
            return
        
        sx = dx > 0 and 1 or -1
        sy = dy > 0 and 1 or -1
        epsilon = 0.000001
        
        fxy = abs(dx)-abs(dy)
        #if fxy==0:
        #    return self.position
        x, y = 0, 0
        try:
            while True:
                if fxy < 0:
                    mx, my = 0, sy
                    fxy += abs(dx)
                else:
                    mx, my = sx, 0
                    fxy -= abs(dy)
                
                self.motor[0].step(mx)
                self.motor[1].step(my)
          
                x += mx
                y += my
                
                self._position = [self._position[0]+mx,
                                  self._position[1]+my,
                                  self.position[2]]
                #self.log.debug("x={} dx={}, y={} dy={}".format(x,dx,y,dy))
                if x == dx and y == dy:
                    break
                
        except KeyboardInterrupt:
             self.disconnect()
             raise
        #self.position = [dx, dy, z]        # Udpate for Inkcut Real-Time Update
        #return self.position               # Update for Inkcut Real-Time Update
    
    def set_velocity(self, v):
        # TODO: Map v to delay
        Device.set_velocity(self, v)
    
    def check_bounds(self):                              # TODO: Develop cutter range check with end stop switches       
        for i in range(self.MAX_X):                     # Move -x until we hit min x bound pin
            self.move(-1, 0)
        for i in range(self.MAX_Y):                     # Move -y until we hit min y bound pin
            self.move(0, -1)
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
        
    def QR_Registration(self, SKU = "VF207" , CameraImage = "QRimageWithGlobals.jpg"):
        if not self.config.crop_mark_registration or not QR_AVAILABLE:
            return 0, 0, 0

        imageRaw = cv2.imread(CameraImage)
        scanner = zbar.ImageScanner()                                        # create a reader
        scanner.parse_config('enable')                                       # configure Reader
        gray = cv2.cvtColor(imageRaw, cv2.COLOR_RGB2GRAY,dstCn=0)            # Obtain image data
        ret, gray = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)            # Threshold to convert image to binary
        
        #gray = cv2.adaptiveThreshold(gray, 255 , cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,17,2)          ## May need integrate this later. Using adaptive gaussian method. Useful for images with ranges of shading in image. Good lighting is probably a better implementation
        
        pil = Image.fromarray(gray)
        width, height = pil.size
        raw = pil.tobytes()
        image = zbar.Image(width,height,'Y800',raw)                          # wrap image data
        scanner.scan(image)    
        
        
        for symbol in scanner.results:
            print(symbol.data)
            print(symbol.location)
            A=symbol.location
            y1a=A[0][1]+0.0                                                  # Corner 0 y point   points to form line a
            y2a=A[2][1]+0.0                                                  # Corner 2 y point
            x1a=A[0][0]+0.0                                                  # Corner 0 x point
            x2a=A[2][0]+0.0                                                  # Corner 2 x point
        
            ma = (y2a-y1a)/(x2a-x1a)                                         # Slope of line a
            ba = y1a - ma*x1a                                                # Intercept of line a
        
            y1b=A[1][1]+0.0                                                  # Corner 1 y point   points to form line b
            y2b=A[3][1]+0.0                                                  # Corner 3 y point
            x1b=A[1][0]+0.0                                                  # Corner 1 x point
            x2b=A[3][0]+0.0                                                  # Corner 3 x point    
        
            mb = (y2b-y1b)/(x2b-x1b)                                         # Slope of line b
            bb = y1b - mb*x1b                                                # Intercept of line b
        
            xintersect = (bb-ba)/(ma-mb)                                     # x intersection point of lines a and b
            yintersect = ma*xintersect + ba                                  # y intersection point of lines a and b
            cv2.circle(imageRaw,(int(xintersect),int(yintersect)),30,(255,0,0),-1)      # draw circles on image for visualization
        
            if (symbol.data == 'CutterTopLeft'):                                  
                CutterTopLeft = (xintersect, yintersect)                     # Save center points of cutter QR codes
            if (symbol.data == 'CutterTopRight'):
                CutterTopRight = (xintersect, yintersect)
            if (symbol.data == 'CutterBottomLeft'):
                CutterBottomLeft = (xintersect, yintersect)
            if (symbol.data == 'CutterBottomRight'):
                CutterBottomRight = (xintersect, yintersect)
            if (symbol.data == SKU+'topLeft'):
                SKUtopLeft = (xintersect, yintersect)                        # Save center points of media QR codes
            if (symbol.data == SKU+'topRight'):
                SKUtopRight = (xintersect, yintersect)
            if (symbol.data == SKU+'bottomLeft'):
                SKUbottomLeft = (xintersect, yintersect)
            if (symbol.data == SKU+'bottomRight'):
                SKUbottomRight = (xintersect, yintersect)
        
        
        
        ##### CUTTER TRANSLATION AND ROTATION CALCULATIONS ########
        
        ma = (CutterBottomRight[1] - CutterTopLeft[1] + 0.0)/(CutterBottomRight[0]-CutterTopLeft[0] + 0.0)     # Slope of line a
        ba = CutterTopLeft[1] - ma*CutterTopLeft[0] + 0.0                                                      # Intercept of line a  
        
        mb = (CutterTopRight[1] - CutterBottomLeft[1] + 0.0)/(CutterTopRight[0] - CutterBottomLeft[0] + 0.0)   # Slope of line b
        bb = CutterBottomLeft[1] - mb*CutterBottomLeft[0] + 0.0                                                # Intercept of line b
        
        xintersect = (bb-ba)/(ma-mb)                                                                           # x intersection point of lines a and b
        yintersect = ma*xintersect + ba                                                                        # y intersection point of lines a and b
        
        CutterTranslation = (xintersect , yintersect)                                                          # Cutter Translation , # Let our rotation metric be the sum of slopes of QR code diagonals
        CutterRotation = (CutterBottomRight[1]-CutterTopLeft[1])/(CutterBottomRight[0]-CutterTopLeft[0]) + (CutterTopRight[1]-CutterBottomLeft[1])/(CutterTopRight[0]-CutterBottomLeft[0]) + 0.0
        
        cv2.line(imageRaw,(int(CutterTopLeft[0]),int(CutterTopLeft[1])),(int(CutterBottomRight[0]),int(CutterBottomRight[1])),(255,0,0),5)
        cv2.line(imageRaw,(int(CutterBottomLeft[0]),int(CutterBottomLeft[1])),(int(CutterTopRight[0]),int(CutterTopRight[1])),(255,0,0),5)
        
        cv2.line(imageRaw,(int(SKUtopLeft[0]),int(SKUtopLeft[1])),(int(SKUbottomRight[0]),int(SKUbottomRight[1])),(0,0,255),5)
        cv2.line(imageRaw,(int(SKUbottomLeft[0]),int(SKUbottomLeft[1])),(int(SKUtopRight[0]),int(SKUtopRight[1])),(0,0,255),5)
        
        
        
        ######### SKU TRANSLATION AND ROTATION CALCULATIONS #########
        
        ma = (SKUbottomRight[1] - SKUtopLeft[1] + 0.0)/(SKUbottomRight[0]-SKUtopLeft[0] + 0.0)                 # Slope of line a
        ba = SKUtopLeft[1] - ma*SKUtopLeft[0] + 0.0                                                            # Intercept of line a  
        
        mb = (SKUtopRight[1] - SKUbottomLeft[1] + 0.0)/(SKUtopRight[0] - SKUbottomLeft[0] + 0.0)               # Slope of line b
        bb = SKUbottomLeft[1] - mb*SKUbottomLeft[0] + 0.0                                                      # Intercept of line b
        
        xintersect = (bb-ba)/(ma-mb)                                                                           # x intersection point of lines a and b
        yintersect = ma*xintersect + ba                                                                        # y intersection point of lines a and b
        
        SKUtranslation = (xintersect , yintersect)                                                             # Cutter Translation , # Let our rotation metric be the sum of slopes of QR code diagonals
        SKUrotation = (SKUbottomRight[1]-SKUtopLeft[1])/(SKUbottomRight[0]-SKUtopLeft[0]) + (SKUtopRight[1]-SKUbottomLeft[1])/(SKUtopRight[0]-SKUbottomLeft[0]) +0.0
        
        
        
        #### TODO: need someway of calibrating Cutter to Image ????????? J
         
        
        ## Matplot lib stuff for visualization  # TODO: replace matplotlib with light weight image viewer
        plt.imshow(imageRaw)
        plt.show()
        x=0                                     # TODO: Solve x translation
        y=0                                     # TODO: Solve y translation
        rotation=0                              # TODO: Solve rotation
        return (x, y, rotation)
    
    

        

