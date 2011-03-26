#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
'''
(C) 2008, 2009 Kerim Mansour
For licensing information please refer to license.txt
'''
from pysvg.animate import *
from pysvg.filter import *
from pysvg.gradient import *
from pysvg.linking import *
from pysvg.script import *
from pysvg.shape import *
from pysvg.structure import *
from pysvg.style import *
from pysvg.text import *

class ShapeBuilder:
    """
    Helper class that creates commonly used objects and shapes with predefined styles and
    few but often used parameters. Used to avoid more complex coding for common tasks.
    """
  
    def createCircle(self, cx, cy, r, strokewidth=1, stroke='black', fill='none'):
        """
        Creates a circle
        @type  cx: string or int
        @param cx:  starting x-coordinate  
        @type  cy: string or int
        @param cy:  starting y-coordinate 
        @type  r: string or int
        @param r:  radius 
        @type  strokewidth: string or int
        @param strokewidth:  width of the pen used to draw
        @type  stroke: string (either css constants like "black" or numerical values like "#FFFFFF")
        @param stroke:  color with which to draw the outer limits
        @type  fill: string (either css constants like "black" or numerical values like "#FFFFFF")
        @param fill:  color with which to fill the element (default: no filling)
        @return:  a circle object
        """
        style_dict = {'fill':fill, 'stroke-width':strokewidth, 'stroke':stroke}
        myStyle = StyleBuilder(style_dict)
        c = circle(cx, cy, r)
        c.set_style(myStyle.getStyle())
        return c
  
    def createEllipse(self, cx, cy, rx, ry, strokewidth=1, stroke='black', fill='none'):
        """
        Creates an ellipse
        @type  cx: string or int
        @param cx:  starting x-coordinate  
        @type  cy: string or int
        @param cy:  starting y-coordinate 
        @type  rx: string or int
        @param rx:  radius in x direction 
        @type  ry: string or int
        @param ry:  radius in y direction
        @type  strokewidth: string or int
        @param strokewidth:  width of the pen used to draw
        @type  stroke: string (either css constants like "black" or numerical values like "#FFFFFF")
        @param stroke:  color with which to draw the outer limits
        @type  fill: string (either css constants like "black" or numerical values like "#FFFFFF")
        @param fill:  color with which to fill the element (default: no filling)
        @return:  an ellipse object
        """
        style_dict = {'fill':fill, 'stroke-width':strokewidth, 'stroke':stroke}
        myStyle = StyleBuilder(style_dict)
        e = ellipse(cx, cy, rx, ry)
        e.set_style(myStyle.getStyle())
        return e
   
    def createRect(self, x, y, width, height, rx=None, ry=None, strokewidth=1, stroke='black', fill='none'):
        """
        Creates a Rectangle
        @type  x: string or int
        @param x:  starting x-coordinate  
        @type  y: string or int
        @param y:  starting y-coordinate 
        @type  width: string or int
        @param width:  width of the rectangle  
        @type  height: string or int
        @param height:  height of the rectangle 
        @type  rx: string or int
        @param rx:  For rounded rectangles, the x-axis radius of the ellipse used to round off the corners of the rectangle. 
        @type  ry: string or int
        @param ry:  For rounded rectangles, the y-axis radius of the ellipse used to round off the corners of the rectangle.
        @type  strokewidth: string or int
        @param strokewidth:  width of the pen used to draw
        @type  stroke: string (either css constants like "black" or numerical values like "#FFFFFF")
        @param stroke:  color with which to draw the outer limits
        @type  fill: string (either css constants like "black" or numerical values like "#FFFFFF")
        @param fill:  color with which to fill the element (default: no filling)
        @return:  a rect object
        """
        style_dict = {'fill':fill, 'stroke-width':strokewidth, 'stroke':stroke}
        myStyle = StyleBuilder(style_dict)
        r = rect(x, y, width, height, rx, ry)
        r.set_style(myStyle.getStyle())
        return r
      
    def createPolygon(self, points, strokewidth=1, stroke='black', fill='none'):
        """
        Creates a Polygon
        @type  points: string in the form "x1,y1 x2,y2 x3,y3"
        @param points:  all points relevant to the polygon
        @type  strokewidth: string or int
        @param strokewidth:  width of the pen used to draw
        @type  stroke: string (either css constants like "black" or numerical values like "#FFFFFF")
        @param stroke:  color with which to draw the outer limits
        @type  fill: string (either css constants like "black" or numerical values like "#FFFFFF")
        @param fill:  color with which to fill the element (default: no filling)
        @return:  a polygon object
        """
        style_dict = {'fill':fill, 'stroke-width':strokewidth, 'stroke':stroke}
        myStyle = StyleBuilder(style_dict)
        p = polygon(points=points)
        p.set_style(myStyle.getStyle())
        return p
      
    def createPolyline(self, points, strokewidth=1, stroke='black'):
        """
        Creates a Polyline
        @type  points: string in the form "x1,y1 x2,y2 x3,y3"
        @param points:  all points relevant to the polygon
        @type  strokewidth: string or int
        @param strokewidth:  width of the pen used to draw
        @type  stroke: string (either css constants like "black" or numerical values like "#FFFFFF")
        @param stroke:  color with which to draw the outer limits
        @return:  a polyline object
        """
        style_dict = {'fill':'none', 'stroke-width':strokewidth, 'stroke':stroke}
        myStyle = StyleBuilder(style_dict)
        p = polyline(points=points)
        p.set_style(myStyle.getStyle())
        return p
        
        
    def createLine(self, x1, y1, x2, y2, strokewidth=1, stroke="black"):
        """
        Creates a line
        @type  x1: string or int
        @param x1:  starting x-coordinate
        @type  y1: string or int
        @param y1:  starting y-coordinate
        @type  x2: string or int
        @param x2:  ending x-coordinate
        @type  y2: string or int
        @param y2:  ending y-coordinate
        @type  strokewidth: string or int
        @param strokewidth:  width of the pen used to draw
        @type  stroke: string (either css constants like "black" or numerical values like "#FFFFFF")
        @param stroke:  color with which to draw the outer limits
        @return:  a line object
        """
        style_dict = {'stroke-width':strokewidth, 'stroke':stroke}
        myStyle = StyleBuilder(style_dict)
        l = line(x1, y1, x2, y2)
        l.set_style(myStyle.getStyle())
        return l
      
    def convertTupleArrayToPoints(self, arrayOfPointTuples):
        """Method used to convert an array of tuples (x,y) into a string
        suitable for createPolygon or createPolyline
        @type  arrayOfPointTuples: An array containing tuples eg.[(x1,y1),(x2,y2]
        @param arrayOfPointTuples:  All points needed to create the shape
        @return a string in the form "x1,y1 x2,y2 x3,y3"
        """
        points = ""
        for tuple in arrayOfPointTuples:
            points += str(tuple[0]) + "," + str(tuple[1]) + " "
        return points



######################################################################
# Style Builder. Utility class to create styles for your shapes etc.
######################################################################
class StyleBuilder:
    """ 
    Class to create a style string for those not familiar with svg attribute names.
    How to use it:
    1) create an instance of StyleBuilder (builder=....)
    2) set the attributes you want to have
    3) create the shape (element) you want
    4) call set_style on the element with "builder.getStyle()" as parameter
    """
    def __init__(self, aStyle_dict=None):
        if aStyle_dict == None:
            self.style_dict = {}
        else:
            self.style_dict = aStyle_dict

  
    # tested below
    def setFontFamily(self, fontfamily):
        self.style_dict["font-family"] = fontfamily
  
    def setFontSize(self, fontsize):
        self.style_dict["font-size"] = fontsize
  
    def setFontStyle(self, fontstyle):
        self.style_dict["font-style"] = fontstyle
  
    def setFontWeight(self, fontweight):
        self.style_dict["font-weight"] = fontweight
    
    #tested
    def setFilling(self, fill):
        self.style_dict["fill"] = fill
  
    def setFillOpacity(self, fillopacity):
        self.style_dict["fill-opacity"] = fillopacity
  
    def setFillRule(self, fillrule):
        self.style_dict["fill-rule"] = fillrule
  
    def setStrokeWidth(self, strokewidth):
        self.style_dict["stroke-width"] = strokewidth
    
    def setStroke(self, stroke):
        self.style_dict["stroke"] = stroke
  
    #untested below  
    def setStrokeDashArray(self, strokedasharray):
        self.style_dict["stroke-dasharray"] = strokedasharray
    def setStrokeDashOffset(self, strokedashoffset):
        self.style_dict["stroke-dashoffset"] = strokedashoffset
    def setStrokeLineCap(self, strikelinecap):
        self.style_dict["stroke-linecap"] = strikelinecap
    def setStrokeLineJoin(self, strokelinejoin):
        self.style_dict["stroke-linejoin"] = strokelinejoin
    def setStrokeMiterLimit(self, strokemiterlimit):
        self.style_dict["stroke-miterlimit"] = strokemiterlimit
    def setStrokeOpacity(self, strokeopacity):
        self.style_dict["stroke-opacity"] = strokeopacity
    

    #is used to provide a potential indirect value (currentColor) for the 'fill', 'stroke', 'stop-color' properties.
    def setCurrentColor(self, color):
        self.style_dict["color"] = color
   
    # Gradient properties:
    def setStopColor(self, stopcolor):
        self.style_dict["stop-color"] = stopcolor
  
    def setStopOpacity(self, stopopacity):
        self.style_dict["stop-opacity"] = stopopacity

    #rendering properties
    def setColorRendering(self, colorrendering):
        self.style_dict["color-rendering"] = colorrendering
   
    def setImageRendering(self, imagerendering):
        self.style_dict["image-rendering"] = imagerendering
    
    def setShapeRendering(self, shaperendering):
        self.style_dict["shape-rendering"] = shaperendering
    
    def setTextRendering(self, textrendering):
        self.style_dict["text-rendering"] = textrendering
    
    def setSolidColor(self, solidcolor):
        self.style_dict["solid-color"] = solidcolor
  
    def setSolidOpacity(self, solidopacity):
        self.style_dict["solid-opacity"] = solidopacity
  
    #Viewport properties  
    def setVectorEffect(self, vectoreffect):
        self.style_dict["vector-effect"] = vectoreffect
    
    def setViewPortFill(self, viewportfill):
        self.style_dict["viewport-fill"] = viewportfill
    
    def setViewPortOpacity(self, viewportfillopacity):
        self.style_dict["viewport-fill_opacity"] = viewportfillopacity
          
    # Text properties
    def setDisplayAlign(self, displayalign):
        self.style_dict["display-align"] = displayalign
    
    def setLineIncrement(self, lineincrement):
        self.style_dict["line-increment"] = lineincrement
    
    def setTextAnchor(self, textanchor):
        self.style_dict["text-anchor"] = textanchor

    #def getStyleDict(self):
    #      return self.style_dict

  
    def getStyle(self):
        string = ''#style="'
        for key, value in self.style_dict.items():
            if value <> None and value <> '':
                string += str(key) + ':' + str(value) + '; '
        return string

######################################################################
# Transform Builder. Utility class to create transformations for your shapes etc.
######################################################################  
class TransformBuilder:
    """ 
      Class to create a transform string for those not familiar with svg attribute names.
      How to use it:
      1) create an instance of TransformBuilder (builder=....)
      2) set the attributes you want to have
      3) create the shape (element) you want
      4) call set_transform on the element with "builder.getTransform()" as parameter
    """
    def __init__(self):
        self.transform_dict = {}
  
    #def setMatrix(self, matrix):
    #    self.transform_dict["matrix"] = 'matrix(%s)' % matrix
  
    def setMatrix(self, a, b, c, d, e, f):
        self.transform_dict["matrix"] = 'matrix(%s %s %s %s %s %s)' % (a, b, c, d, e, f)
  
    def setRotation(self, rotate):
        self.transform_dict["rotate"] = 'rotate(%s)' % rotate
  
    #def setRotation(self, rotation, cx=None, cy=None):
    #    if cx != None and cy != None:
    #        self.transform_dict["rotate"] = 'rotate(%s %s %s)' % (rotation, cx, cy)
    #    else:
    #        self.transform_dict["rotate"] = 'rotate(%s)' % (rotation)
    
    def setTranslation(self, translate):
        self.transform_dict["translate"] = 'translate(%s)' % (translate)
  
    #def setTranslation(self, x, y=0):
    #    self.transform_dict["translate"] = 'translate(%s %s)' % (x, y)
    
    #def setScaling(self, scale):
    #    self.transform_dict["scale"] = 'scale(%s)' % (scale)
  
    def setScaling(self, x=None, y=None):
        if x == None and y != None:
            x = y
        elif x != None and y == None:
            y = x
        self.transform_dict["scale"] = 'scale(%s %s)' % (x, y)
  
    def setSkewY(self, skewY):
        self.transform_dict["skewY"] = 'skewY(%s)' % (skewY)
  
    def setSkewX(self, skewX):
        self.transform_dict["skewX"] = 'skewX(%s)' % (skewX)
 
    #def getTransformDict(self):
    #  return self.transform_dict
    
    def getTransform(self):
        string = ''#style="'
        for key, value in self.transform_dict.items():
            if value <> None and value <> '':
                #string+=str(key)+':'+str(value)+'; '
                string += str(value) + ' '
        return string
