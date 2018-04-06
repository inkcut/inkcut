"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import os
import re
import sys
import logging
from enaml.image import Image
from enaml.icon import Icon, IconImage
from enaml.application import timed_call
from twisted.internet.defer import Deferred


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


# -----------------------------------------------------------------------------
# Unit conversion
# -----------------------------------------------------------------------------
unit_conversions = {'in': 90.0, 'pt': 1.25, 'px': 1, 'mm': 3.5433070866,
           'cm': 35.433070866, 'm': 3543.3070866,
           'km': 3543307.0866, 'pc': 15.0, 'yd': 3240, 'ft': 1080}

def from_unit(val, unit='px'):
    return unit_conversions[unit]*val


def to_unit(val, unit='px'):
    return val/unit_conversions[unit]


def parse_unit(value):
    """ Parse a string into pixels """
    if isinstance(value, (int, float)):
        raise ValueError("No unit found in '%s', unitless values only have meaning in the context of a specifc SVG document" % value)

    unit = re.compile('(%s)$' % '|'.join(unit_conversions.keys()))
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
            return retval * unit_conversions[u.string[u.start():u.end()]]
        except KeyError:
            raise ValueError("No unit found in '%s', unitless values only have meaning in the context of a specifc SVG document" % value)
    else:
        raise ValueError("No unit found in '%s', unitless values only have meaning in the context of a specifc SVG document" % value)
    return retval



# -----------------------------------------------------------------------------
# Async helpers
# -----------------------------------------------------------------------------
def async_sleep(ms):
    """ Sleep for the given duration without blocking. Typically this
    is used with the inlineCallbacks decorator.
    """
    d = Deferred()
    timed_call(ms, d.callback, True)
    return d