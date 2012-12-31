# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2011 Jairus Martin - Vinylmark LLC <jrm@vinylmark.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE
import tempfile
import os
import inspect
import logging
import glob
from inkcut_lib.geom import geom,bezmisc
from inkcut_lib.filters.filter import Filter
from inkcut_lib.filters.hpgl import SVGtoHPGL, HPGLtoSVG

logger = logging.getLogger('inkcut')
__all__ = [os.path.basename(f)[:-3] for f in glob.glob(os.path.join(os.path.abspath(os.path.dirname(__file__)),"*.py"))]

class NoFilterFoundException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value) 

def convert(infile,preferences,outfile=None,inext=None,outext=None):
    #TODO: read filter registration file to find filters
    if inext is None:
        inext = os.path.splitext(infile)[1][1:]
    if outext is None:
        if outfile:
            outext = os.path.splitext(outfile)[1][1:]
        else:
            outext = preferences['device']['cmd_language'].lower()
    logger.info("Searching for a %s to %s filter..."%(inext,outext))
    for ftr in get_filters():
        if (outext == ftr.outfiletype) and (inext in ftr.infiletypes):
            logger.info("Found the %s filter."%ftr.name)
            f = ftr(infile,outfile,preferences)
            f.run()
            return f.outfile
    logger.info("No filter found...")
    raise NoFilterFoundException("No filter found for converting %s type to %s type..."%(inext,outext))


def get_filters():
    """ Returns a list of any class in the filters package that subclasses the filter class."""
    # TOOD: figure out how to actually do this...
    #import inkcut_lib.filters
    #for name in inkcut_lib.filters.__all__:
    #    if name != "__init__":
    #        module = __import__('inkcut_lib.filters.%s'%name)
    #        print module
    return [SVGtoHPGL,HPGLtoSVG,Filter]

if __name__ == "__main__":
    get_filters()