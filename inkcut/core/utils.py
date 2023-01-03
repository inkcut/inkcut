"""
Copyright (c) 2017-2020, the Inkcut team.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import os
import sys
import logging
from enaml.colors import Color
from enaml.image import Image
from enaml.icon import Icon, IconImage
from enaml.application import timed_call
from enaml.qt.QtCore import QPointF
from enaml.qt.QtGui import QPainterPath, QPixmap, QIcon
from enaml.qt.q_resource_helpers import get_cached_qcolor
from twisted.internet.defer import Deferred
from .svg import QtSvgDoc


# -----------------------------------------------------------------------------
# Logger
# -----------------------------------------------------------------------------
log = logging.getLogger("inkcut")


def clip(s, n=1000):
    """ Shorten the name of a large value when logging"""
    v = str(s)
    if len(v) > n:
        v[:n]+"..."
    return v

# -----------------------------------------------------------------------------
# Icon and Image helpers
# -----------------------------------------------------------------------------
#: Cache for icons
_IMAGE_CACHE = {}


def icon_path(name):
    """ Load an icon from the res/icons folder using the name
    without the .png

    """
    path = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(path, 'res', 'icons', '%s.png' % name)


def load_image(name):
    """ Get and cache an enaml Image for the given icon name.

    """
    path = icon_path(name)
    global _IMAGE_CACHE
    if path not in _IMAGE_CACHE:
        with open(path, 'rb') as f:
            data = f.read()
        _IMAGE_CACHE[path] = Image(data=data)
    return _IMAGE_CACHE[path]


def load_icon(name):
    img = load_image(name)
    icg = IconImage(image=img)
    return Icon(images=[icg])


def menu_icon(name):
    """ Icons don't look good on Linux/osx menu's """
    if sys.platform == 'win32':
        return load_icon(name)
    return None


def color_icon(color):
    pixmap = QPixmap(12, 12)
    if color is None:
        color = Color(0, 0, 0, 0)
    pixmap.fill(get_cached_qcolor(color))
    icg = IconImage(image=Image(_tkdata=pixmap.toImage()))
    return Icon(images=[icg])


# -----------------------------------------------------------------------------
# Unit conversion
# -----------------------------------------------------------------------------
def from_unit(val, unit='px'):
    return QtSvgDoc.convertFromUnit(val, unit)


def to_unit(val, unit='px'):
    return QtSvgDoc.convertToUnit(val, unit)


def parse_unit(val):
    """ Parse a string into pixels """
    return QtSvgDoc.parseUnit(val)


unit_conversions = QtSvgDoc._uuconv

# -----------------------------------------------------------------------------
# Async helpers
# -----------------------------------------------------------------------------
def async_sleep(ms):
    """ Sleep for the given duration without blocking. Typically this
    is used with the inlineCallbacks decorator.
    """
    d = Deferred()
    timed_call(int(ms), d.callback, True)
    return d


# -----------------------------------------------------------------------------
# QPainterPath helpers
# -----------------------------------------------------------------------------
def split_painter_path(path):
    """ Split a QPainterPath into subpaths. """
    if not isinstance(path, QPainterPath):
        raise TypeError("path must be a QPainterPath, got: {}".format(path))

    # Element types
    MoveToElement = QPainterPath.MoveToElement
    LineToElement = QPainterPath.LineToElement
    CurveToElement = QPainterPath.CurveToElement
    CurveToDataElement = QPainterPath.CurveToDataElement

    subpaths = []
    params = []
    e = None

    def finish_curve(p, params):
        if len(params) == 2:
            p.quadTo(*params)
        elif len(params) == 3:
            p.cubicTo(*params)
        else:
            raise ValueError("Invalid curve parameters: {}".format(params))

    for i in range(path.elementCount()):
        e = path.elementAt(i)

        # Finish the previous curve (if there was one)
        if params and e.type != CurveToDataElement:
            finish_curve(p, params)
            params = []

        # Reconstruct the path
        if e.type == MoveToElement:
            p = QPainterPath()
            p.moveTo(e.x, e.y)
            subpaths.append(p)
        elif e.type == LineToElement:
            p.lineTo(e.x, e.y)
        elif e.type == CurveToElement:
            params = [QPointF(e.x, e.y)]
        elif e.type == CurveToDataElement:
            params.append(QPointF(e.x, e.y))

    # Finish the previous curve (if there was one)
    if params:
        finish_curve(p, params)
    return subpaths


def join_painter_paths(paths):
    """ Join a list of QPainterPath into a single path """
    result = QPainterPath()
    for p in paths:
        result.addPath(p)
    return result

MoveToElement = QPainterPath.MoveToElement
LineToElement = QPainterPath.LineToElement
CurveToElement = QPainterPath.CurveToElement
CurveToDataElement = QPainterPath.CurveToDataElement
def add_item_to_path(result, e, i, elements):
    if type(elements) is QPainterPath:
        element_count = elements.elementCount()
        get_element = elements.elementAt
    else:
        element_count = len(elements)
        get_element = elements.__getitem__

    position = path_element_to_point(e)
    if e.type == MoveToElement:
        result.moveTo(position)
    elif e.type == LineToElement:
        result.lineTo(position)
    elif e.type == CurveToElement:
        params = [position]
        j = i + 1
        while j < element_count:
            next_item = get_element(j)
            if next_item.type != CurveToDataElement:
                break
            params.append(path_element_to_point(next_item))
            j += 1
        if len(params) == 2:
            result.quadTo(*params)
        elif len(params) == 3:
            result.cubicTo(*params)
        else:
            raise ValueError("Invalid curve parameters: {}".format(params))
    elif e.type == CurveToDataElement:
        pass  # already processed
    else:
        raise ValueError("Unexpected curve element type: {}".format(e.type))

def path_to_elements(path):
    """ Create list of QPainterPath.Element to QPainterPath

    """
    return [path.elementAt(i) for i in range(path.elementCount())]

def path_from_elements(elements):
    """ Convert list of QPainterPath.Element to QPainterPath

    """
    result = QPainterPath()
    for i, e in enumerate(elements):
        add_item_to_path(result, e, i, elements)
    return result

def path_element_to_point(element):
    return QPointF(element.x, element.y)

def trailing_angle(path):
    if path.elementCount() < 10:
        return path.angleAtPercent(1)
    else:
        p = QPainterPath()
        p.reserve(10)
        pos = path.elementCount() - 5
        while pos < path.elementCount():
            add_item_to_path(p, path.elementAt(pos), pos, path)
            pos += 1
        return p.angleAtPercent(1)


def find_subclasses(cls):
    """ Finds all known (imported) subclasses of the given class """
    cmds = []
    for subclass in cls.__subclasses__():
        cmds.append(subclass)
        cmds.extend(find_subclasses(subclass))
    return cmds
