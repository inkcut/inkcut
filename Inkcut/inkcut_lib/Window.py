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

from gi.repository import Gtk, Gdk, GObject # pylint: disable=E0611

import logging
logger = logging.getLogger('inkcut_lib')

from . helpers import get_builder, show_uri, get_help_uri, callback,InkcutUIState

# This class is meant to be subclassed by InkcutWindow.  It provides
# common functions and some boilerplate.
class Window(Gtk.Window,InkcutUIState):
    __gtype_name__ = "Window"
    state_key = "plot"
    # To construct a new instance of this method, the following notable 
    # methods are called in this order:
    # __new__(cls)
    # __init__(self)
    # finish_initializing(self, builder)
    # __init__(self)
    #
    # For this reason, it's recommended you leave __init__ empty and put
    # your initialization code in finish_initializing
    
    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated BaseInkcutWindow object.
        """
        builder = get_builder('InkcutWindow')
        new_object = builder.get_object("inkcut_window")
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called while initializing this instance in __new__

        finish_initializing should be called after parsing the UI definition
        and creating a InkcutWindow object with it in order to finish
        initializing the start of the new InkcutWindow instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self, True)
        
        self.PreferencesDialog = None # class
        self.preferences_dialog = None # instance
        
        self.DeviceDialog = None # class
        self.device_dialog = None # instance
        
        self.MaterialDialog = None # class
        self.material_dialog = None # instance
        
        self.AboutDialog = None # class

        #preferences.connect('changed', self.on_preferences_changed)

        # Optional Launchpad integration
        # This shouldn't crash if not found as it is simply used for bug reporting.
        # See https://wiki.ubuntu.com/UbuntuDevelopment/Internationalisation/Coding
        # for more information about Launchpad integration.
        try:
            from gi.repository import LaunchpadIntegration # pylint: disable=E0611
            LaunchpadIntegration.add_items(self.ui.helpMenu, 1, True, True)
            LaunchpadIntegration.set_sourcepackagename('inkcut')
        except ImportError:
            pass

        # Optional application indicator support
        # Run 'quickly add indicator' to get started.
        # More information:
        #  http://owaislone.org/quickly-add-indicator/
        #  https://wiki.ubuntu.com/DesktopExperienceTeam/ApplicationIndicators
        try:
            from inkcut import indicator
            # self is passed so methods of this class can be called from indicator.py
            # Comment this next line out to disable appindicator
            self.indicator = indicator.new_application_indicator(self)
        except ImportError:
            pass

    def on_act_help_activate(self, widget, data=None):
        show_uri(self, "ghelp:%s" % get_help_uri())

    def on_act_about_activate(self, widget, data=None):
        """Display the about box for inkcut."""
        if self.AboutDialog is not None:
            about = self.AboutDialog() # pylint: disable=E1102
            response = about.run()
            about.destroy()

    def on_act_inkcut_prefs_activate(self, widget, data=None):
        """Display the preferences window for inkcut."""

        """ From the PyGTK Reference manual
           Say for example the preferences dialog is currently open,
           and the user chooses Preferences from the menu a second time;
           use the present() method to move the already-open dialog
           where the user can see it."""
        if self.preferences_dialog is not None:
            logger.debug('show existing preferences_dialog')
            self.preferences_dialog.present()
        elif self.PreferencesDialog is not None:
            logger.debug('create new preferences_dialog')
            self.preferences_dialog = self.PreferencesDialog() # pylint: disable=E1102
            self.preferences_dialog.connect('destroy', self.on_preferences_dialog_destroyed)
            self.preferences_dialog.show()
        # destroy command moved into dialog to allow for a help button
        
    def on_act_device_manager_activate(self,widget,data=None):
        """Display the device dialog."""
        if self.device_dialog is not None:
            logger.debug('show existing device_dialog')
            self.device_dialog.present()
        elif self.DeviceDialog is not None:
            logger.debug('create new device_dialog')
            self.device_dialog = self.DeviceDialog() # pylint: disable=E1102
            self.device_dialog.toplevel = False
            self.device_dialog.connect('destroy', self.on_device_dialog_destroyed)
            self.device_dialog.show()
            
    def on_act_media_manager_activate(self,widget,data=None):
        """Display the material dialog."""
        if self.material_dialog is not None:
            logger.debug('show existing material_dialog')
            self.material_dialog.present()
        elif self.MaterialDialog is not None:
            logger.debug('create new material_dialog')
            self.material_dialog = self.MaterialDialog() # pylint: disable=E1102
            self.material_dialog.toplevel = False
            self.material_dialog.connect('destroy', self.on_material_dialog_destroyed)
            self.material_dialog.show()

    def on_act_quit_activate(self, widget, data=None):
        """Signal handler for closing the InkcutWindow."""
        self.destroy()

    def on_destroy(self, widget, data=None):
        """Called when the InkcutWindow is closed."""
        # Clean up code for saving application state should be added here.
        # Save the current app settings
        logger.debug('Window.on_destroy()')
        self.save_state('app')
        Gtk.main_quit()

    def on_preferences_changed(self, widget, data=None):
        logger.debug('main window received preferences changed')
        #for key in data:
        #    logger.debug('preference changed: %s = %s' % (key, preferences[key]))

    def on_preferences_dialog_destroyed(self, widget, data=None):
        """ Remove the preferences_dialog instance """
        logger.debug('Window.on_preferences_dialog_destroyed()')
        # to determine whether to create or present preferences_dialog
        self.preferences_dialog = None
    
    def on_device_dialog_destroyed(self, widget, data=None):
        """ Remove the device_dialog instance """
        logger.debug('Window.on_device_dialog_destroyed()')
        # to determine whether to create or present device_dialog
        self.device_dialog = None

    def on_material_dialog_destroyed(self, widget, data=None):
        """ Remove the material_dialog instance """
        logger.debug('Window.on_material_dialog_destroyed()')
        # to determine whether to create or present material_dialog
        self.material_dialog = None
        
    def on_tb_compact_menu_clicked(self, widget, data=None):
        """ Show the compact menu """
        logger.debug('Window.on_tb_compact_menu_clicked()')
        self.ui['compact_menu'].popup(None, None, None, None, Gdk.BUTTON_PRIMARY,0)
