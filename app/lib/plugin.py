#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: plugin.py
# Author: Copyright 2011 Jairus Martin <frmdstryr@gmail.com>
# Date: 27 July 2011
#
# License:
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
import logging
log = logging.getLogger(__name__)

"""
1) Inkcut loads all plugins in the plugins folder into the application database.
    The plugin class name, mode, and attr's related to that mode are pickled.
        For either mode:
            the name registered is the class name minus "Plugin",
                (eg. HPGLPlugin would be entered as HPGL)
            the mode registered is the result of Plugin.mode attribute,
                this attribute must be either "import" or "export", otherwise
                an error will result.
            the filetype registered is the result of Plugin.filetype attribute,
                this attribute must return a string containing the filetype extension

2) Import Plugin:
    a) Invoked when Inkcut attempts to open a file with the registered filetype
    extension.

    b) The Plugin.input attribute is set to the absolute path of the input file.

    c) The Plugin.run() method is called

    d) Inkcut attempts to create a plot by parsing the value of the
    Plugin.output attribute.  Allowed types are file and string.  It must be
    a file parseable by lxml.etree.fromstring() or lxml.etree.parse().

3) Export Plugin:
    a) Invoked when a job containing this output filetype:
        1. is sent to a device.
        2. is asked to create an exact output preview.
    b) The Plugin.input attribute is set to the absolute path of the temporary
    Job output SVG file.
        The following properties will be passed as

    c) The Plugin.run() method is called

    d) Inkcut sends the value of Plugin.output to the device queue.

"""

class Plugin(object):
    """
    Base class for defining an Inkcut plugin.  There are two modes: input
    and output.  An input plugin is used for converting filetype x into an
    SVG file, which is then read by Inkcut. An output plugin is used for
    converting a SVG file into an output filetype.
    """
    def __init__(self):
        self.name = None
        self.mode = None
        self.filetypes = []
        self.input = None
        self.output = None

    def init_export(self,plot,device):
        """
        Initializes the variables available to an export plugin.  This should
        be pushed into the Inkcut application.
        """
        self.plot = {                   # ==== Updated with value ====
            'width':None,               # plot.get_width()
            'height':None,              # plot.get_height()
            'path_length':None,         # plot.get_length()
            'finish_position':(0,0),    # inkcut.get_final_position()
        }
        self.plot.update(plot)

        self.device = {                                     # ==== Updated with value ====
            'axis_translate':(0,0)                          # device.get_axis_translate()
            'axis_scale':(1,1)                              # device.get_axis_scale()
            'axis_rotation':0,                              # device.get_axis_rotation()
            'cutting_overlap':(10,True),                    # device.get_cutting_overlap(),device.get_cutting_overlape_status()
            'cutting_blade_offset':(0.88582675,True),       # device.get_cutting_blade_offset(), device.get_cutting_blade_offset_status()
            'cutting_force':(80,False), # Value, Enabled    # device.get_cutting_force(), device.get_cutting_force_status()
            'cutting_speed':(8,False), # Value, Enabled     # device.get_cutting_speed(), device.get_cutting_speed_status()
        }

        self.commands {           # ==== Updated with value ====
            'send_before':[],     # inkcut.plugin.get_commands_before()
            'send_after':[],      # inkcut.plugin.get_commands_after()
        }

    def run(self):
        """ Converts self.input into self.output. """
        pass

    # ====================== Common Export Functions ==========================
    def apply_cutting_overlap(self,data,overlap):
        """Applies a cutting overlap to a Graphic.get_path_array(). Returns None."""
        pass
    def apply_cutting_blade_offset(self,data,offset):
        """Applies a cutting blade offset to a Graphic.get_path_array(). Returns None."""
        pass

    # ===================== UI & Error Handling ===============================
    def handle_failure(self,message):
        """ Prompts the user with an error message and tells Inkcut the plugin failed."""
        pass

    def alert_user(self,message,type_):
        """Used for raising errors and sending messages to the Inkcut UI """
        pass

    def prompt_user(self,message,gtk_dialog=None):
        """ Prompts the user for input with the given message type. """
        pass


