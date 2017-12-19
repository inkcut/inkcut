# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Parses an SVG document into a QPainterPath. Adapted from inkscape's path 
parsers written by Aaron Spike.

Created on Jan 5, 2015

@author: Jairus Martin, frmdstryr@gmail.com
@author: Aaron Spike, aaron@ekips.org
"""
import re
import math
from lxml import etree
from copy import deepcopy
from enaml.qt import QtGui, QtCore
from future.builtins import str

ElementType = QtGui.QPainterPath.ElementType
EtreeElement = etree._Element


class QtSvgItem(QtGui.QPainterPath):
    tag = None
    
    _uuconv = {'in': 90.0, 'pt': 1.25, 'px': 1, 'mm': 3.5433070866,
               'cm': 35.433070866, 'm': 3543.3070866,
               'km': 3543307.0866, 'pc': 15.0, 'yd': 3240, 'ft': 1080}
    
    def __init__(self, e, *args, **kwargs):
        if not isinstance(e, EtreeElement):
            raise TypeError("%s only works with etree Elements, "
                            "given %s" % (self, type(e)))
        elif e.tag != self.tag:
            raise ValueError("%s only works with %s elements, "
                             "given %s" % (self, self.tag, e.tag))
        super(QtSvgItem, self).__init__(*args, **kwargs)
        
        self._e = e
        
        # Parse from node
        self.parse(e)
        
        # Parse transform
        self *= self.parseTransform(e)
        
    def __imul__(self, m):
        """ Do in place multiplication by subtracting everything from itself 
        then adding the multiplied values back. 
        """
        tmp = self*m
        self -= self
        self += tmp
        return self
    
    @staticmethod
    def toSubpathList(self):
        paths = []
        path = QtGui.QPainterPath()
        i = 0
        while i < self.elementCount():
            e = self.elementAt(i)
            if e.type == ElementType.MoveToElement:
                if not path.isEmpty():
                    paths.append(path)
                path = QtGui.QPainterPath(QtCore.QPointF(e.x, e.y))
            elif e.type == ElementType.LineToElement:
                path.lineTo(QtCore.QPointF(e.x, e.y))
            elif e.type == ElementType.CurveToElement:
                e1, e2 = self.elementAt(i+1), self.elementAt(i+2)
                path.cubicTo(QtCore.QPointF(e.x, e.y),
                             QtCore.QPointF(e1.x, e1.y),
                             QtCore.QPointF(e2.x, e2.y))
                i += 2
            else:
                raise ValueError("Invalid element type %s" % (e.type,))
            i += 1
        if not path.isEmpty():
            paths.append(path)
        return paths
    
    @staticmethod
    def splitAtPercent(self, t):
        paths = []
        path = QtGui.QPainterPath()
        i = 0
        while i < self.elementCount():
            e = self.elementAt(i)
            if e.type == ElementType.MoveToElement:
                if not path.isEmpty():
                    paths.append(path)
                path = QtGui.QPainterPath(QtCore.QPointF(e.x, e.y))
            elif e.type == ElementType.LineToElement:
                path.lineTo(QtCore.QPointF(e.x, e.y))
            elif e.type == ElementType.CurveToElement:
                e1, e2 = self.elementAt(i+1), self.elementAt(i+2)
                path.cubicTo(QtCore.QPointF(e.x, e.y),
                             QtCore.QPointF(e1.x, e1.y),
                             QtCore.QPointF(e2.x, e2.y))
                i += 2
            else:
                raise ValueError("Invalid element type %s" % (e.type,))
            i += 1
        if not path.isEmpty():
            paths.append(path)
        return paths
    
    @staticmethod
    def parseUnit(string):
        """ Returns userunits given a string representation of units 
        in another system
        """
        if not isinstance(string, str):
            return string
        unit = re.compile('(%s)$' % '|'.join(QtSvgItem._uuconv.keys()))
        param = re.compile(
            r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')
    
        p = param.match(string)
        u = unit.search(string)    
        if p:
            retval = float(p.string[p.start():p.end()])
        else:
            retval = 0.0
        if u:
            try:
                return retval * QtSvgItem._uuconv[u.string[u.start():u.end()]]
            except KeyError:
                pass
        return retval
    
    @staticmethod
    def convertToUnit(val, unit='px'):
        """ Convert from px to given unit """
        return val/QtSvgItem._uuconv[unit]
    
    @staticmethod
    def convertFromUnit(val, unit='px'):
        """ Convert from given unit to px """
        return QtSvgItem._uuconv[unit]*val
        
    def parse(self, e):
        raise NotImplementedError("Parse must be implemented in sublcasses!")
    
    def parseTransform(self, e):
        """ Based on simpletrasnform.py by from 
        Jean-Francois Barraud, barraud@math.univ-lille1.fr

        """
        t = QtGui.QTransform()
        
        if isinstance(e, EtreeElement):
            trans = e.attrib.get('transform', '').strip()
        else:
            trans = e # e is a string of the previous transform
        
        if not trans:
            return t
        
        m = re.match(
            "(translate|scale|rotate|skewX|skewY|matrix)\s*\(([^)]*)\)\s*,?",
            trans)
        if m is None:
            return t
        
        name, args = m.group(1), m.group(2).replace(',', ' ').split()
        
        if name == "translate":
            dx = float(args[0])
            dy = len(args) == 2 and float(args[1]) or dx
            t.translate(dx, dy)
            
        elif name == "scale":
            sx = float(args[0])
            sy = len(args) == 2 and float(args[1]) or sx
            t.scale(sx, sy)
             
        elif name == "rotate":
            if len(args) == 1:
                cx, cy = (0, 0)
            else:
                cx, cy = map(float, args[1:])
            
            t.translate(-cx, -cy)
            t.rotate(float(args[0]))
            t.translate(cx, cy)
            
        elif name == "skewX":
            t.shear(math.tan(float(args[0])*math.pi/180.0), 0)

        elif name == "skewY":
            t.shear(0, math.tan(float(args[0])*math.pi/180.0))
            
        elif name == "matrix":
            t = t*QtGui.QTransform(*map(float, args))
        
        if m.end() < len(trans):
            t = self.parseTransform(trans[m.end():])*t
            
        return t

    def __str__(self):
        return self.tag


class QtSvgEllipse(QtSvgItem):
    tag = "{http://www.w3.org/2000/svg}ellipse"
    
    def parse(self, e):
        c = QtCore.QPointF(*map(self.parseUnit, (e.attrib.get('cx', 0),
                                                 e.attrib.get('cy', 0))))
        rx, ry = map(self.parseUnit, (e.attrib.get('rx', 0),
                                      e.attrib.get('ry', 0)))
        self.addEllipse(c, rx, ry)


class QtSvgCircle(QtSvgItem):
    tag = "{http://www.w3.org/2000/svg}circle"
    
    def parse(self,e):
        c = QtCore.QPointF(*map(self.parseUnit, (e.attrib.get('cx', 0),
                                                 e.attrib.get('cy', 0))))
        r = self.parseUnit(e.attrib.get('r', 0))
        self.addEllipse(c, r, r)


class QtSvgLine(QtSvgItem):
    tag = "{http://www.w3.org/2000/svg}line"
    
    def parse(self,e):
        x1, y1, x2, y2 = map(self.parseUnit, (
                e.attrib.get('x1', 0), e.attrib.get('y1', 0),
                e.attrib.get('x2', 0), e.attrib.get('y2', 0),
        ))
        self.moveTo(x1, y1)
        self.lineTo(x2, y2)


class QtSvgRect(QtSvgItem):
    tag = "{http://www.w3.org/2000/svg}rect"
    
    def parse(self, e):
        x, y, w, h, rx, ry = map(self.parseUnit, (
                    e.attrib.get('x', 0), e.attrib.get('y', 0),
                    e.attrib.get('width', 0), e.attrib.get('height', 0),
                    e.attrib.get('rx', 0), e.attrib.get('ry', 0),
                )
        )
        
        if rx == 0 and ry == 0:
            self.addRect(x, y, w, h)
        else: 
            if rx == 0:
                rx = ry
            else:
                ry = rx
            self.addRoundedRect(x, y, w, h, rx, ry)


class QtSvgPath(QtSvgItem):
    tag = "{http://www.w3.org/2000/svg}path"
    
    # From  simplepath.py's parsePath by Aaron Spike, aaron@ekips.org
    pathdefs = {
        'M': ['L', 2, [float, float], ['x', 'y']],
        'L': ['L', 2, [float, float], ['x', 'y']],
        'H': ['H', 1, [float], ['x']],
        'V': ['V', 1, [float], ['y']],
        'C': ['C', 6, [float, float, float, float, float, float],
                        ['x', 'y', 'x', 'y', 'x', 'y']],
        'S': ['S', 4, [float, float, float, float], ['x', 'y', 'x', 'y']],
        'Q': ['Q', 4, [float, float, float, float], ['x', 'y', 'x', 'y']],
        'T': ['T', 2, [float, float], ['x', 'y']],
        'A': ['A', 7, [float, float, float, int, int, float, float],
                        ['r', 'r', 'a', 0, 's', 'x', 'y']],
        'Z': ['L', 0, [], []]
    }
    
    def parsePathData(self, e):
        return e.attrib.get('d', '')
    
    def parse(self, e):
        d = self.parsePathData(e)
        if not d:
            return
        
        for cmd, params in self.parsePath(d):
            if cmd == 'M':
                self.moveTo(*params)
            elif cmd == 'C':
                self.cubicTo(*params)
            elif cmd in ['L', 'H', 'V']:
                self.lineTo(*params)
            elif cmd == 'Q':
                self.quadTo(*params)
            elif cmd == 'A':
                self.arcTo(*params)
            elif cmd == 'Z':
                self.closeSubpath()

    def pathLexer(self, d):
        """
        From  simplepath.py's parsePath by Aaron Spike, aaron@ekips.org

        returns and iterator that breaks path data 
        identifies command and parameter tokens
        """
        offset = 0
        length = len(d)
        delim = re.compile(r'[ \t\r\n,]+')
        command = re.compile(r'[MLHVCSQTAZmlhvcsqtaz]')
        parameter = re.compile(
            r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')
        while True:
            m = delim.match(d, offset)
            if m:
                offset = m.end()
            if offset >= length:
                break
            m = command.match(d, offset)
            if m:
                yield [d[offset:m.end()], True]
                offset = m.end()
                continue
            m = parameter.match(d, offset)
            if m:
                yield [d[offset:m.end()], False]
                offset = m.end()
                continue
            raise ValueError('Invalid path data at %s!' % offset)
        
    def parsePath(self, d):
        """
        From  simplepath.py's parsePath by Aaron Spike, aaron@ekips.org
        
        Parse SVG path and return an array of segments.
        Removes all shorthand notation.
        Converts coordinates to absolute.
        """
        lexer = self.pathLexer(d)
    
        pen = (0.0,0.0)
        subPathStart = pen
        lastControl = pen
        lastCommand = ''
        
        while True:
            try:
                token, isCommand = next(lexer)
            except StopIteration:
                break
            params = []
            needParam = True
            if isCommand:
                if not lastCommand and token.upper() != 'M':
                    raise ValueError('Invalid path, must begin with moveto ('
                                     'M or m), given %s.' % lastCommand)
                else:                
                    command = token
            else:
                # command was omited
                # use last command's implicit next command
                needParam = False
                if lastCommand:
                    if lastCommand.isupper():
                        command = self.pathdefs[lastCommand][0]
                    else:
                        command = self.pathdefs[lastCommand.upper()][0].lower()
                else:
                    raise ValueError('Invalid path, no initial command.')    
            numParams = self.pathdefs[command.upper()][1]
            while numParams > 0:
                if needParam:
                    try: 
                        token, isCommand = next(lexer)
                        if isCommand:
                            raise ValueError('Invalid number of parameters '
                                             'for %s' % (command, ))
                    except StopIteration:
                        raise Exception('Unexpected end of path')
                cast = self.pathdefs[command.upper()][2][-numParams]
                param = cast(token)
                if command.islower():
                    if self.pathdefs[command.upper()][3][-numParams] == 'x':
                        param += pen[0]
                    elif self.pathdefs[command.upper()][3][-numParams] == 'y':
                        param += pen[1]
                params.append(param)
                needParam = True
                numParams -= 1
            # segment is now absolute so
            outputCommand = command.upper()
        
            # Flesh out shortcut notation
            if outputCommand in ('H', 'V'):
                if outputCommand == 'H':
                    params.append(pen[1])
                if outputCommand == 'V':
                    params.insert(0, pen[0])
                outputCommand = 'L'
            if outputCommand in ('S', 'T'):
                params.insert(0,pen[1]+(pen[1]-lastControl[1]))
                params.insert(0,pen[0]+(pen[0]-lastControl[0]))
                if outputCommand == 'S':
                    outputCommand = 'C'
                if outputCommand == 'T':
                    outputCommand = 'Q'
    
            # current values become "last" values
            if outputCommand == 'M':
                subPathStart = tuple(params[0:2])
                pen = subPathStart
            if outputCommand == 'Z':
                pen = subPathStart
            else:
                pen = tuple(params[-2:])
    
            if outputCommand in ('Q', 'C'):
                lastControl = tuple(params[-4:-2])
            else:
                lastControl = pen
            
            lastCommand = command
    
            yield [outputCommand, params]


class QtSvgPolyline(QtSvgPath):
    tag = "{http://www.w3.org/2000/svg}polyline"
    
    def parsePathData(self, e):
        d = e.attrib.get('points', '')
        if not d:
            return 
        
        return 'M '+d


class QtSvgPolygon(QtSvgPolyline):
    tag = "{http://www.w3.org/2000/svg}polygon"
    
    def parsePathData(self,e):
        d = super(QtSvgPolygon, self).parsePathData(e)
        if not d:
            return
        return d+' Z'


class QtSvgUse(QtSvgItem):
    tag = "{http://www.w3.org/2000/svg}use"
    xlink = "{http://www.w3.org/1999/xlink}href"
    
    def parseLink(self,e):
        link = e.attrib.get(self.xlink, '').split("#")
        if len(link) != 2:
            raise NotImplementedError(
                    "Cannot link to documents outside this "
                    "document, given %s!" % ("#".join(link),))
        link, id = link
        
        svg = e.getroottree().getroot()
        ref = svg.xpath('//*[@id="%s"]' % id)
        if len(ref) > 0:
            return ref[0]
        
    def parse(self, e):
        ref = self.parseLink(e)
        if ref is None:
            return
        elif ref.tag == QtSvgSymbol.tag:
            self.addPath(QtSvgSymbol(ref))
        else:
            g = etree.Element(QtSvgG.tag)
            g.append(deepcopy(ref))
            self.addPath(QtSvgG(g))
            
    def parseTransform(self, e):
        t = super(QtSvgUse, self).parseTransform(e)
        if isinstance(e, EtreeElement):
            x, y = map(self.parseUnit, (e.attrib.get('x', 0),
                                        e.attrib.get('y', 0)))
            t.translate(x, y)
        return t


class QtSvgText(QtSvgItem):
    tag = "{http://www.w3.org/2000/svg}text"
    
    stylemap = {
        'normal': QtGui.QFont.StyleNormal,
        'italic': QtGui.QFont.StyleItalic,
        'oblique': QtGui.QFont.StyleOblique
    }
    
    def parse(self, e):
        x, y = map(self.parseUnit, (e.attrib.get('x', 0),
                                    e.attrib.get('y', 0)))
        font = self.parseFont(e)
        self.addText(x, y, font, e.text)
    
    def parseFont(self, e):
        """
        font-style:italic;
        font-variant:normal;
        font-weight:500;
        font-stretch:normal;
        font-size:40px;
        line-height:125%;
        font-family:Ubuntu;
        -inkscape-font-specification:'Ubuntu, Medium Italic';
        text-align:start;
        letter-spacing:0px;
        word-spacing:0px;
        writing-mode:lr-tb;
        text-anchor:start;
        fill:#000000;
        fill-opacity:1;
        stroke:none;
        stroke-width:1px;
        stroke-linecap:butt;
        stroke-linejoin:miter;
        stroke-opacity:1
        
        """
        font = QtGui.QFont()
        styles = {}
        for item in e.attrib.get('style', '').split(";"):
            k, v = item.split(":")
            styles[k.lower()] = v.lower()
        
        if 'font-style' in styles:
            font.setStyle(self.stylemap.get(
                styles['font-style'].lower(), 'normal'))
        # if 'font-variant' in styles:
        if 'font-weight' in styles:
            font.setWeight(self.parseUnit(styles['font-weight']))
        if 'font-stretch' in styles:
            font.setStretch(self.parseUnit(styles['font-stretch']))
        if 'font-size' in styles:
            font.setPixelSize(self.parseUnit(styles['font-size']))
        if 'font-family' in styles:
            font.setFamily(styles['font-family'])
        # if 'line-height' in styles:
        #    font.setLineHeight(self.parseUnit(styles['font-size']))
        return font


class QtSvgG(QtSvgItem):
    tag = "{http://www.w3.org/2000/svg}g"
    
    def parse(self, e):
        for node in e:
            if node.tag == QtSvgText.tag:
                raise ValueError("Text nodes are not supported. "
                                 "Please convert all text to paths and "
                                 "re-open the document.")

            for cls in [
                        QtSvgG,
                        QtSvgDoc,
                        QtSvgPath,
                        QtSvgRect,
                        QtSvgCircle,
                        QtSvgEllipse,
                        QtSvgPolygon,
                        QtSvgPolyline,
                        QtSvgLine,
                        QtSvgUse,
                        #QtSvgText
                    ]:
                if node.tag == cls.tag:
                    self.addPath(cls(node))
                    break
    

class QtSvgSymbol(QtSvgG):
    tag = "{http://www.w3.org/2000/svg}symbol"


class QtSvgDoc(QtSvgG):
    tag = "{http://www.w3.org/2000/svg}svg"
    
    def __init__(self, e):
        """
        Creates a QtPainterPath from an SVG document applying all transforms. 
        
        Does NOT include any styling.
        
        @param e: An lxml etree.Element or an argument to pass to etree.parse()
        """
        self.isParentSvg = not isinstance(e, EtreeElement)
        
        if self.isParentSvg:
            self._doc = etree.parse(e)
            self._svg = self._doc.getroot()
            self.viewBox = QtCore.QRectF(0, 0, -1, -1)
        
        super(QtSvgDoc, self).__init__(self._svg)
    
    def parseTransform(self, e):
        t = QtGui.QTransform()
        # transforms don't apply to the root svg element
        if not self.isParentSvg:
            x, y = map(self.parseUnit, (e.attrib.get('x', 0),
                                        e.attrib.get('y', 0)))
            t.translate(x, y)
            
        # TODO: Handle width/height and viewBox stuff
        #         else:
        #             w,h = map(self.parseUnit,(e.attrib.get('width',None),
        # e.attrib.get('height',None)))
        #             if w is not None or h is not None:
        #                 sx,sy = 
        #             
            
        return t
