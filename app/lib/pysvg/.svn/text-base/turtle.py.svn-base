'''
(C) 2008, 2009, 2010 Kerim Mansour
For licensing information please refer to license.txt
'''
import math
from shape import polyline

class Vector(object):
    """
    Class representing a vector. Used to determine position of the turtle as well as heading.
    Also used to calculate movement.
    Vector class is inspired by tips and code from:
    - http://slowchop.com/2006/07/15/a-fast-python-vector-class/
    - http://www.kokkugia.com/wiki/index.php5?title=Python_vector_class
    - http://xturtle.rg16.at/code/xturtle.py
    """
    __slots__ = ('x', 'y')    
    def __init__(self, x, y):
        """ Initializes the vector. 
        x and y are coordinates and should be numbers. 
        They will be cast to floats
        """ 
        self.x = float(x)
        self.y = float(y)
    
    def __add__(self, vector):
        return Vector(self.x + vector.x, self.y + vector.y)
    
    def __sub__(self, vector):
        return Vector(self.x - vector.x, self.y - vector.y)
    
    def __mul__(self, vector):
        if isinstance(vector, Vector):
            return self.x * vector.x + self.y * vector.y
        return Vector(self.x * vector, self.y * vector)
    
    def __rmul__(self, vector):
        if isinstance(vector, int) or isinstance(vector, float):
            return Vector(self.x * vector, self.y * vector)
    
    def __neg__(self):
        return Vector(-self.x, -self.y)
    
    def __abs__(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5
    
    def rotate(self, angle):
        """Rotates self counterclockwise by angle 
        (the angle must be given in a 360 degree system)
        """
        perp = Vector(-self.y, self.x)
        angle = angle * math.pi / 180.0
        c, s = math.cos(angle), math.sin(angle)
        return Vector(self.x * c + perp.x * s, self.y * c + perp.y * s)
    
    def __getnewargs__(self):
        return (self.x, self.y)
    
    def __repr__(self):
        return "%.2f,%.2f " % (self.x, self.y) 
    
class Turtle(object):
    """
    Class representing a classical turtle object known from logo and other implementations.
    Note that currently each turtle has exactly ONE style of drawing, so if you intend to draw in multiple styles several instances of turtles are needed.
    A turtle will only actually draw when the pen is down (default=false).
    An xml representation usable for pysvg can ge retrieved using the getXML()-method.
    To add the turtles paths to an svg you have two opions:
    Either you simply call "addTurtlePathToSVG" or you can create an svg element and append the Elements of the turtle using a loop, e.g:
    s=svg(...)
    t=Turtle(...)
    for element in t.getSVGElements():
        s.addElement(element)
    """
    def __init__(self, initialPosition=Vector(0.0, 0.0), initialOrientation=Vector(1.0, 0.0), fill='white', stroke='black', strokeWidth='1', penDown=False):
        """ Initializes a new Turtle with a new initial position and orientation as well as defaultvalues for style.
        """
        self.fill = fill
        self.stroke = stroke
        self.strokeWidth = strokeWidth
        self._position = initialPosition
        self._orient = initialOrientation
        self._penDown = penDown
        self._svgElements = []
        self._pointsOfPolyline = []
    
        
    def forward(self, distance):
        """ Moves the turtle forwards by distance in the direction it is facing. 
        If the pen is lowered it will also add to the currently drawn polyline.
        """
        self._move(distance)
    
    def backward(self, distance):
        """ Moves the turtle backwards by distance in the direction it is facing. 
        If the pen is lowered it will also add to the currently drawn polyline.
        """
        self._move(-distance)
    
    def right(self, angle):
        """Rotates the turtle to the right by angle.
        """
        self._rotate(angle)
    
    def left(self, angle):
        """Rotates the turtle to the left by angle.
        """
        self._rotate(-angle)
    
    def moveTo(self, vector):
        """ Moves the turtle to the new position. Orientation is kept as it is. 
        If the pen is lowered it will also add to the currently drawn polyline.
        """
        self._position = vector
        if self.isPenDown(): 
            self._pointsOfPolyline.append(self._position)
    
    def penUp(self):
        """ Raises the pen. Any movement will not draw lines till pen is lowered again.
        """
        if self._penDown==True:
            self._penDown = False
            self._addPolylineToElements()
    
    def penDown(self):
        """ Lowers the pen down again. A new polyline will be created for drawing.
        Old polylines will be stored in the stack
        """
        #if self._penDown==False:
        self._penDown = True
        self._addPolylineToElements()
    
    def finish(self):
        """MUST be called when drawing is finished. Else the last path will not be added to the stack.
        """
        self._addPolylineToElements()
        
    def isPenDown(self):
        """ Retrieve current status of the pen.(boolean)
        """
        return self._penDown
    
    def getPosition(self):
        """ Retrieve current position of the turtle.(Vector)
        """
        return self._position
    
    def getOrientation(self):
        """ Retrieve current orientation of the turtle.(Vector)
        """
        return self._orient
    
    def setOrientation(self, vec):
        """ Sets the orientation of the turtle.(Vector)
        """
        self._orient=vec
    
    def _move(self, distance):
        """ Moves the turtle by distance in the direction it is facing. 
        If the pen is lowered it will also add to the currently drawn polyline.
        """
        self._position = self._position + self._orient * distance  
        if self.isPenDown(): 
            x = round(self._position.x, 2)
            y = round(self._position.y, 2)
            self._pointsOfPolyline.append(Vector(x, y))
        
    def _rotate(self, angle):
        """Rotates the turtle.
        """
        self._orient = self._orient.rotate(angle)
        
    def _addPolylineToElements(self):
        """Creates a new Polyline element that will be used for future movement/drawing. 
        The old one (if filled) will be stored on the movement stack.
        """
        if (len(self._pointsOfPolyline) > 1):
            s = ''
            for point in self._pointsOfPolyline:
                s += str(point) + ' '#str(point.x) + ',' + str(point.y) + ' '
            p = polyline(s)
            p.set_style('fill:' + self.fill + '; stroke:' + self.stroke + '; stroke-width:' + self.strokeWidth) 
            self._svgElements.append(p)
        self._pointsOfPolyline = []
        self._pointsOfPolyline.append(Vector(self._position.x, self._position.y))
    
    def getXML(self):
        """Retrieves the pysvg elements that make up the turtles path and returns them as String in an xml representation.
        """
        s = ''
        for element in self._svgElements:
            s += element.getXML()
        return s

    def getSVGElements(self):
        """Retrieves the pysvg elements that make up the turtles path and returns them as list.
        """
        return self._svgElements
    
    def addTurtlePathToSVG(self, svgContainer):
        """Adds the paths of the turtle to an existing svg container.
        """
        for element in self.getSVGElements():
            svgContainer.addElement(element)
        return svgContainer
    