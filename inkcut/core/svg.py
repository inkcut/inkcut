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
from math import sqrt, tan, atan, atan2, cos, acos, sin, pi, radians
from lxml import etree
from copy import deepcopy
from enaml.qt import QtGui, QtCore
from inkcut.core.layers import layers, Layer

ElementType = QtGui.QPainterPath.ElementType
EtreeElement = etree._Element


class QtSvgItem(QtGui.QPainterPath):
    tag = None
    _nodes = None
    _uuconv = {'in': 90.0, 'pt': 1.25, 'px': 1, 'mm': 3.5433070866,
               'cm': 35.433070866, 'm': 3543.3070866,
               'km': 3543307.0866, 'pc': 15.0, 'yd': 3240, 'ft': 1080}

    def __init__(self, e, nodes=None, **kwargs):
        if not isinstance(e, EtreeElement):
            raise TypeError("%s only works with etree Elements, "
                            "given %s" % (self, type(e)))
        elif e.tag != self.tag:
            raise ValueError("%s only works with %s elements, "
                             "given %s" % (self, self.tag, e.tag))
        super(QtSvgItem, self).__init__(**kwargs)

        self._nodes = nodes
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
    def parseUnit(value):
        """ Returns userunits given a string representation of units
        in another system
        """

        if value is None:
            return None

        if isinstance(value, (int, float)):
            return value

        unit = re.compile('(%s)$' % '|'.join(QtSvgItem._uuconv.keys()))
        param = re.compile(
            r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')

        p = param.match(value)
        u = unit.search(value)
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
            # The translate(<x> [<y>]) transform function moves the object
            # by x and y. If y is not provided, it is assumed to be 0.
            dx = float(args[0])
            dy = float(args[1]) if len(args) == 2 else 0
            t.translate(dx, dy)

        elif name == "scale":
            # The scale(<x> [<y>]) transform function specifies a scale
            # operation by x and y. If y is not provided, it is assumed to
            # be equal to x.
            sx = float(args[0])
            sy = float(args[1]) if len(args) == 2 else sx
            t.scale(sx, sy)

        elif name == "rotate":
            # The rotate(<a> [<x> <y>]) transform function specifies a
            # rotation by a degrees about a given point. If optional
            # parameters x and y are not supplied, the rotation is about the
            # origin of the current user coordinate system. If optional
            # parameters x and y are supplied, the rotation is about the
            # point (x, y).
            if len(args) == 1:
                cx, cy = (0, 0)
            else:
                cx, cy = map(float, args[1:])

            t.translate(cx, cy)
            t.rotate(float(args[0]))
            t.translate(-cx, -cy)

        elif name == "skewX":
            # The skewX(<a>) transform function specifies a skew transformation
            # along the x axis by a degrees.
            t.shear(math.tan(float(args[0])*math.pi/180.0), 0)

        elif name == "skewY":
            # The skewY(<a>) transform function specifies a skew transformation
            # along the y axis by a degrees.
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

    def parse(self, e):
        c = QtCore.QPointF(*map(self.parseUnit, (e.attrib.get('cx', 0),
                                                 e.attrib.get('cy', 0))))
        r = self.parseUnit(e.attrib.get('r', 0))
        self.addEllipse(c, r, r)


class QtSvgLine(QtSvgItem):
    tag = "{http://www.w3.org/2000/svg}line"

    def parse(self, e):
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
            elif ry == 0:
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
                        ['r', 'r', 'a', 'a', 's', 'x', 'y']],
        'Z': ['L', 0, [], []]
    }

    def parsePathData(self, e):
        return e.attrib.get('d', '')

    def arc(self, x1, y1, rx, ry, phi, large_arc_flag, sweep_flag, x2o, y2o):

        # handle rotated arcs as normal arcs that are transformed as a rotation
        if phi != 0:
            x2 = x1 + (x2o - x1)*cos(radians(phi)) + (y2o - y1)*sin(radians(phi))
            y2 = y1 - (x2o - x1)*sin(radians(phi)) + (y2o - y1)*cos(radians(phi))
        else:
            x2, y2 = x2o, y2o

        # https://www.w3.org/TR/SVG/implnote.html F.6.6
        rx = abs(rx)
        ry = abs(ry)

        # https://www.w3.org/TR/SVG/implnote.html F.6.5
        x1prime = (x1 - x2)/2
        y1prime = (y1 - y2)/2

        # https://www.w3.org/TR/SVG/implnote.html F.6.6
        lamb = (x1prime*x1prime)/(rx*rx) + (y1prime*y1prime)/(ry*ry)
        if lamb >= 1:
            ry = sqrt(lamb)*ry
            rx = sqrt(lamb)*rx

        # Back to https://www.w3.org/TR/SVG/implnote.html F.6.5
        radicand = (rx*rx*ry*ry - rx*rx*y1prime*y1prime - ry*ry*x1prime*x1prime)
        radicand /= (rx*rx*y1prime*y1prime + ry*ry*x1prime*x1prime)

        if radicand < 0:
            radicand = 0

        factor = (-1 if large_arc_flag == sweep_flag else 1)*sqrt(radicand)

        cxprime = factor*rx*y1prime/ry
        cyprime = -factor*ry*x1prime/rx

        cx = cxprime + (x1 + x2)/2
        cy = cyprime + (y1 + y2)/2

        start_theta = -atan2((y1 - cy) * rx, (x1 - cx) * ry)

        start_phi = -atan2(y1 - cy, x1 - cx)
        end_phi = -atan2(y2 - cy, x2 - cx)

        sweep_length = end_phi - start_phi

        if sweep_length < 0 and not sweep_flag:
            sweep_length += 2 * pi
        elif sweep_length > 0 and sweep_flag:
            sweep_length -= 2 * pi

        if phi != 0:
            rotarc = QtGui.QPainterPath()
            rotarc.moveTo(x1, y1)
            rotarc.arcTo(cx - rx, cy - ry, rx * 2, ry * 2,
                start_theta * 360 / 2 / pi, sweep_length * 360 / 2 / pi)

            t = QtGui.QTransform()
            t.translate(x1, y1)
            t.rotate(phi)
            t.translate(-x1, -y1)
            tmp = rotarc*t
            rotarc -= rotarc
            rotarc += tmp
            self.addPath(rotarc)

        else:
            self.arcTo(cx - rx, cy - ry, rx * 2, ry * 2,
                       start_theta * 360 / 2 / pi, sweep_length * 360 / 2 / pi)


    def parse(self, e):
        d = self.parsePathData(e)
        if not d:
            return

        for cmd, params in self.parsePath(d):
            if cmd == 'M':
                self.moveTo(*params)
                mx, my = params[0], params[1]
            elif cmd == 'C':
                self.cubicTo(*params)
            elif cmd in ['L', 'H', 'V']:
                self.lineTo(*params)
            elif cmd == 'Q':
                self.quadTo(*params)
            elif cmd == 'A':
                x1 = self.currentPosition().x()
                y1 = self.currentPosition().y()
                (rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, x2, y2) = params
                self.arc(x1, y1, rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, x2, y2)

            elif cmd == 'Z':
                self.lineTo(mx, my)  # not self.closeSubpath() as arc() may have internal moveTo calls

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

        pen = (0.0, 0.0)
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

    def parsePathData(self, e):
        d = super(QtSvgPolygon, self).parsePathData(e)
        if not d:
            return
        return d+' Z'


class QtSvgUse(QtSvgItem):
    tag = "{http://www.w3.org/2000/svg}use"
    xlink = "{http://www.w3.org/1999/xlink}href"

    def parseLink(self, e):
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
            self.addPath(QtSvgSymbol(ref, self._nodes))
        else:
            g = etree.Element(QtSvgG.tag)
            g.append(deepcopy(ref))
            self.addPath(QtSvgG(g, self._nodes))

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

        # An inkscape Layer definition in this G group ?
        if e.get ("{http://www.inkscape.org/namespaces/inkscape}groupmode") == "layer":
            name = e.get ("{http://www.inkscape.org/namespaces/inkscape}label")
            for l in layers:
                #if layer is disabled or not loaded, do not add the branch
                if name == l.name:
                    if not l.enabled or not l.loaded:
                        return
                    #update the transform to offset the layer
                    e.set ("transform", "translate(" + str(l.offsetX) + ","  + str(l.offsetY) +")" )
                    break

        valid_nodes = self._nodes
        for node in e:
            if node.tag == QtSvgText.tag:
                raise ValueError("Text nodes are not supported. "
                                 "Please convert all text to paths and "
                                 "re-open the document.")
            if valid_nodes and node not in valid_nodes:
                continue

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
                    self.addPath(cls(node, valid_nodes))
                    break


class QtSvgSymbol(QtSvgG):
    tag = "{http://www.w3.org/2000/svg}symbol"

class QtSvgScanLayers(QtSvgG):

    def __init__(self, e):
        """
        Count and register G tags that are Inkscape Layers
        Parameters
        ----------
            e: Element or string
                An lxml etree.Element or an argument to pass to etree.parse()
        """
        # clear previous Layers info
        del layers [:]
        doc = etree.parse(e)
        svg = doc.getroot()
        for node in svg.iter("{http://www.w3.org/2000/svg}g"):
            if node.get ("{http://www.inkscape.org/namespaces/inkscape}groupmode") == "layer":
                l = Layer()
                l.name = node.get ("{http://www.inkscape.org/namespaces/inkscape}label")
                l.offsetX = 0
                l.offsetY = 0
                l.enabled = True
                if node.get ("style") is not None:
                    l.loaded = re.match ("display:.*inline", node.get ("style") ) is not None
                #log.info("Accepted Layer :" + l.name +" enabled:"+str(l.enabled))
                #TODO: append only Layers that have something displayable
                layers.append(l)

class QtSvgDoc(QtSvgG):
    tag = "{http://www.w3.org/2000/svg}svg"

    def __init__(self, e, ids=None):
        """
        Creates a QtPainterPath from an SVG document applying all transforms.

        Does NOT include any styling.

        Parameters
        ----------
            e: Element or string
                An lxml etree.Element or an argument to pass to etree.parse()
            ids: List
                List of node ids to include. If not given all will be used.
        """
        self.isParentSvg = not isinstance(e, EtreeElement)
        if self.isParentSvg:
            self._doc = etree.parse(e)
            self._svg = self._doc.getroot()
            if ids:
                nodes = set()
                xpath = self._svg.xpath
                for node_id in ids:
                    nodes.update(set(xpath('//*[@id="%s"]' % node_id)))

                # Find all nodes and their parents
                valid_nodes = set()
                for node in nodes:
                    valid_nodes.add(node)
                    parent = node.getparent()
                    while parent:
                        valid_nodes.add(parent)
                        parent = parent.getparent()
                self._nodes = valid_nodes

            self.viewBox = QtCore.QRectF(0, 0, -1, -1)

        super(QtSvgDoc, self).__init__(self._svg, self._nodes)

    def parseTransform(self, e):
        t = QtGui.QTransform()
        # transforms don't apply to the root svg element, but we do need to
        # take into account the viewBox there
        if self.isParentSvg:
            viewBox = e.attrib.get('viewBox', None)
            if viewBox is not None:
                (x, y, innerWidth, innerHeight) = map(self.parseUnit,
                                                      re.split("[ ,]+",
                                                               viewBox))

                if x != 0 or y != 0:
                    raise ValueError(
                        "viewBox '%s' needs to be translated "
                        "because is not at the origin. "
                        "See https://github.com/codelv/inkcut/issues/69"
                        % viewBox)

                outerWidth, outerHeight = map(self.parseUnit,
                                              (e.attrib.get('width', None),
                                               e.attrib.get('height', None)))
                if outerWidth is not None and outerHeight is not None:
                    t.scale(outerWidth / innerWidth, outerHeight / innerHeight)
        else:
            x, y = map(self.parseUnit, (e.attrib.get('x', 0),
                                        e.attrib.get('y', 0)))
            t.translate(x, y)

        return t
