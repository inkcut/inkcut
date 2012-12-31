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

import argparse
import json
import tempfile
import os

import gettext
from gettext import gettext as _
gettext.textdomain('inkcut')

from gi.repository import Gtk # pylint: disable=E0611

from inkcut import InkcutWindow,DeviceDialog, AboutInkcutDialog, StatusDialog

from inkcut_lib import set_up_logging, get_version
from inkcut_lib import filters,preferences
from inkcut_lib.device import Device
from inkcut_lib.preferences import CONFIG_FILE,DEFAULT_PREFERENCES # using data/preferences.json

def parse_args():
    """Support for command line options"""
    parser = argparse.ArgumentParser(version="%%prog %s" % get_version())
    parser.add_argument(
        "--verbose", action="count", dest="verbose",
        help=_("Show debug messages (-vv debugs inkcut_lib also)"))
    parser.add_argument(
        "--show-dialog",choices=['DeviceProperties','AboutInkcut'],#,'control_dialog','materials_dialog']
        dest="dialog",
        help=_("Run an Inkcut dialog."))
    parser.add_argument(
        "--plot",dest="filename",
        help=_("Send a file of plot data to the device."))
    parser.add_argument(
        "--plugin",dest="plugin",
        help=_("Call if runing using a plugin."))
    group = parser.add_argument_group('Conversion')    
    group.add_argument(
        "--convert",nargs=2,
        help=_("Use inkcut --convert infile.ext outfile.out. Conversion type is determined by the output file extension."))
    group.add_argument(
        "--input-type",dest='inext',
        help=_("Convert from this input type."))
    group.add_argument(
        "--output-type",dest='outext',
        help=_("Convert to this output type."))
    args = parser.parse_args()
    set_up_logging(args)
    return args

def main():
    args = parse_args()
    
    # Do an action depending on the arguments
    if args.dialog:
        if args.dialog=='DeviceProperties':
            dialog = DeviceDialog.DeviceDialog()
            dialog.show()
            Gtk.main()
        elif args.dialog=='AboutInkcut':
            dialog = AboutInkcutDialog.AboutDialog()
            dialog.show()
            Gtk.main()
        """ Coming eventually...
        elif args.dialog=='control_dialog':
            pass
        elif args.dialog=='materials_dialog':
            pass
        """
    elif args.convert:
        filters.convert(infile=args.convert[0],preferences=preferences.load(),outfile=args.convert[1],inext=args.inext,outext=args.outext)
    elif args.filename:
        dialog = StatusDialog.StatusDialog()
        dialog.plot(args.filename,args.plugin)
        dialog.show()
        Gtk.main()
        if args.plugin=='inkscape':
            os.remove(args.filename)

            
    else:
        window = InkcutWindow.InkcutWindow()
        window.show()
        Gtk.main()
    
