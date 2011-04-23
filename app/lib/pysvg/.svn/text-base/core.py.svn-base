#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
'''
(C) 2008, 2009 Kerim Mansour
For licensing information please refer to license.txt
'''
from attributes import CoreAttrib, ConditionalAttrib, StyleAttrib, GraphicalEventsAttrib, PaintAttrib, OpacityAttrib, GraphicsAttrib, CursorAttrib, FilterAttrib, MaskAttrib, ClipAttrib
    
class BaseElement:
    """
    This is the base class for all svg elements like title etc. It provides common functionality.
    It should NOT be directly used by anyone.
    """
    def __init__(self, elementName):
        """
        initializes the object
        @type  elementName: string 
        @param elementName:  name of the element (used for the xml tag) 
        """
        self._elementName=elementName
        self._attributes={}  #key value
        self._textContent=""
        self._subElements=[]
    
    def appendTextContent(self,text):
        self.addElement(TextContent(text))
        
    def addElement(self,element):
        self._subElements.append(element)
    
    def getElementAt(self,pos):
        """ returns the element at a specific position within this svg
        """
        return self._subElements[pos]
    
    def getAllElements(self):
        """ returns all elements contained within the top level element list of this element
        """
        return self._subElements
    
    def getAllElementsOfHirarchy(self):
        """ returns ALL elements of the complete hirarchy as a flat list
        """
        allElements=[]
        for element in self.getAllElements():
            allElements.append(element)
            if isinstance(element, BaseElement):
                allElements.extend(element.getAllElementsOfHirarchy())
        return allElements
    
    def getElementByID(self, id):
        """ returns an element with the specific id and the position of that element within the svg elements array
        """
        pos=0
        for element in self._subElements:
            if element.get_id()==id:
                return (element,pos)
            pos+=1
    
    def getElementsByType(self, type):
        """
        retrieves all Elements that are of type type
        @type  type: class 
        @param type:  type of the element 
        """
        foundElements=[]
        for element in self.getAllElementsOfHirarchy():
            if isinstance(element, type):
                foundElements.append(element)                
                
        return foundElements
    
    def insertElementAt(self, element, pos):
        return self._subElements.insert(pos, element)
    
        
    def getXML(self):
        """
        Return a XML representation of the current element.
        This function can be used for debugging purposes. It is also used by getXML in SVG
    
        @return:  the representation of the current element as an xml string
        """
        xml='<'+self._elementName+' '
        for key,value in self._attributes.items():
            if value != None:
                xml+=key+'="'+self.quote_attrib(str(value))+'" '
        if  len(self._subElements)==0: #self._textContent==None and
            xml+=' />\n'
        else:
            xml+=' >\n'
            #if self._textContent==None:
            for subelement in self._subElements:
                xml+=str(subelement.getXML())
            #else:
            #if self._textContent!=None:
            #    xml+=self._textContent
            xml+='</'+self._elementName+'>\n'
        #print xml
        return xml

    #generic methods to set and get atributes (should only be used if something is not supported yet
    def setAttribute(self, attribute_name, attribute_value):
        self._attributes[attribute_name]=attribute_value
    
    def getAttribute(self, attribute_name):
        return self._attributes.get(attribute_name)
    
    def getAttributes(self):
        """ get all atributes of the element
        """
        return self._attributes

    def setKWARGS(self, **kwargs):
        """ 
        Used to set all attributes given in a **kwargs parameter.
        Might throw an Exception if attribute was not found.
        #TODO: check if we should fix this using "setAttribute"
        """
        for key in kwargs.keys():
            #try:
            f = getattr(self,'set_' + key)
            f(kwargs[key])
            #except:
            #    print('attribute not found via setter ')
            #    self.setAttribute(self, key, kwargs[key])
            
    def wrap_xml(self, xml, encoding ='ISO-8859-1', standalone='no'):
        """
        Method that provides a standard svg header string for a file
        """
        header = '''<?xml version="1.0" encoding="%s" standalone="%s"?>''' %(encoding, standalone)
        return  header+xml
    
    def save(self, filename, encoding ='ISO-8859-1', standalone='no'):
        """
        Stores any element in a svg file (including header). 
        Calling this method only makes sense if the root element is an svg elemnt
        """
        f = open(filename, 'w')
        f.write(self.wrap_xml(self.getXML(), encoding, standalone))
        f.close()
        
    def quote_attrib(self, inStr):
        """
        Transforms characters between xml notation and python notation.
        """
        s1 = (isinstance(inStr, basestring) and inStr or
              '%s' % inStr)
        s1 = s1.replace('&', '&amp;')
        s1 = s1.replace('<', '&lt;')
        s1 = s1.replace('>', '&gt;')
        if '"' in s1:
        #    if "'" in s1:
            s1 = '%s' % s1.replace('"', "&quot;")
        #    else:
        #        s1 = "'%s'" % s1
        #else:
        #    s1 = '"%s"' % s1
        return s1
    
class TextContent:
    """
    Class for the text content of an xml element. Can also include PCDATA
    """
    def __init__(self,content):
        self.content=content
    def setContent(self,content):
        self.content=content
    def getXML(self):
        return self.content
    def get_id(self):
        return None
    
#--------------------------------------------------------------------------#
# Below are classes that define attribute sets that pysvg uses for convenience.
# There exist no corresponding attribute sets in svg.
# We simply use these classes as containers for often used attributes.
#--------------------------------------------------------------------------#
class PointAttrib:
    """
    The PointAttrib class defines x and y.
    """
    def set_x(self, x):
        self._attributes['x']=x
    def get_x(self):
        return self._attributes.get('x')
    
    def set_y(self, y):
        self._attributes['y']=y
    def get_y(self):
        return self._attributes.get('y')

class DeltaPointAttrib:
    """
    The DeltaPointAttrib class defines dx and dy.
    """
    def set_dx(self, dx):
        self._attributes['dx']=dx
    def get_dx(self):
        return self._attributes.get('dx')
    
    def set_dy(self, dy):
        self._attributes['dy']=dy
    def get_dy(self):
        return self._attributes.get('dy')
    
class PointToAttrib:
    """
    The PointToAttrib class defines x2 and y2.
    """
    def set_x2(self, x2):
        self._attributes['x2']=x2
    def get_x2(self):
        return self._attributes.get('x2')
    
    def set_y2(self, y2):
        self._attributes['y2']=y2
    def get_y2(self):
        return self._attributes.get('y2')
    
class DimensionAttrib:
    """
    The DimensionAttrib class defines height and width.
    """
    def set_height(self, height):
        self._attributes['height']=height
    
    def get_height(self):
        return self._attributes.get('height')
    
    def set_width(self, width):
        self._attributes['width']=width
    
    def get_width(self):
        return self._attributes.get('width')

class RotateAttrib:
    """
    The RotateAttrib class defines rotation.
    """
    def set_rotate(self, rotate):
        self._attributes['rotate']=rotate
    
    def get_rotate(self):
        return self._attributes.get('rotate')

class BaseShape(BaseElement, CoreAttrib, ConditionalAttrib, StyleAttrib, GraphicalEventsAttrib, PaintAttrib, OpacityAttrib, GraphicsAttrib, CursorAttrib, FilterAttrib, MaskAttrib, ClipAttrib):
    """
    Baseclass for all shapes. Do not use this class directly. There is no svg element for it
    """
    def set_transform(self, transform):
        self._attributes['transform']=transform
    def get_transform(self):
        return self._attributes.get('transform') 
