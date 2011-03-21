#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       inkcut.py
#
#       Copyright 2010 Jairus Martin <jrm5555@psu.edu>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
import sys,os,logging,pygtk
pygtk.require('2.0')
import gtk
import ConfigParser
import lib
from lib.unit import unit
from lib.meta import Session
from lib.job import Job
from lib.serial import scan
from lxml import etree
from sqlalchemy import engine_from_config

# Load Configuration Files
config = ConfigParser.RawConfigParser()
dirname = os.path.dirname
config.read(os.path.join(dirname(__file__),'config','app.cfg'))
if os.name == 'nt':
    sys.path.append(config.get('Inkscape','win_extension_dir'))
elif os.name == 'posix':
    import cups
    sys.path.append(config.get('Inkscape','extension_dir'))
import inkex


class Application(object):
    """
    Inkcut application, handles gui and device/job interaction
    """

    def __init__(self):
        """Load initial application settings from database """
        engine = engine_from_config(dict(config.items('Inkcut')),'sqlalchemy.')
        Session.configure(bind=engine)
        self.job = None
        self.ui = {
            'main_window':MainWindow(self),
            'device_dialog':DeviceDialog(self),
        }
        self.statusbar = self.ui['main_window'].widgets['statusbar']

    def run(self):
        """Starts the application and builds the gui"""
        self.ui['main_window'].widgets['main'].show_all()
        gtk.main()

    def load(self,source=None,source_filename=None,selected_nodes=None):
        job = Job()
        if job.load(source=source,source_filename=source_filename,selected_nodes=selected_nodes):
            # update the ui with job info
            self.job = job
            self._flash(0,'%s loaded'%os.path.basename(job.source_filename or 'File'))
            self._update_preview()
            return True
        else:
            msg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                buttons=gtk.BUTTONS_CLOSE,
                message_format=job.messages.pop())
            msg.set_title('Error opening file')
            msg.run()
            msg.destroy()
            return False

    def _update_preview(self):
        """ Refreshes the preview """
        loader = gtk.gdk.PixbufLoader('svg')
        loader.write(etree.tostring(self.job.data))
        loader.close()
        self.ui['main_window'].widgets['preview'].set_from_pixbuf(loader.get_pixbuf())

    def _flash(self,id,msg,duration=30.0):
        """ Flash a message in the statusbar """
        if duration>0:
            pass #gtk.timeout_add(duration,'')
        return self.statusbar.push(id,msg)


class UserInterface(object):
    """ Shared UI functions and methods """
    def keep_widgets(self,builder,widgets):
        """
        Keeps the only the widgets we need from the builder so the
        builder can be destroyed and memory can be freed up
        """
        keep = {}
        for widget in widgets:
            w = builder.get_object(widget)
            if w != 0: keep[widget] = w
        return keep


    # Builder Helpers
    def set_adjustment_values(self,builder,etree):
        """ Glade default adjustment values fix """
        for object in etree.xpath('/interface/object[@class="GtkAdjustment"]'):
            property = object.xpath('property[@name="value"]')
            if len(property):
                obj = builder.get_object(object.get('id'))
                obj.set_value(float(property[0].text))

    def get_combobox_active_text(self,combobox):
       model = combobox.get_model()
       active = combobox.get_active()
       if active < 0:
          return None
       return model[active][0]

    def set_model_from_list (self,cb, items):
        """Setup a ComboBox or ComboBoxEntry based on a list of strings."""
        model = gtk.ListStore(str)
        for i in items:
            model.append([i])
        cb.set_model(model)
        if type(cb) == gtk.ComboBoxEntry:
            cb.set_text_column(0)
        elif type(cb) == gtk.ComboBox:
            cell = gtk.CellRendererText()
            cb.pack_start(cell, True)
            cb.add_attribute(cell, 'text', 0)

    # Common Signals
    def gtk_main_quit(self, window):
        """ Quit the application """
        gtk.main_quit()

    def gtk_window_hide(self,window):
        """ Hide a window """
        self.window.hide();



class MainWindow(UserInterface):
    def __init__(self,app):
        """ Builds the main window """
        self.app = app
        builder = gtk.Builder()

        # TODO: fix this
        glade_file = os.path.join(os.path.abspath(dirname(__file__)),'ui','main-window.glade')
        builder.add_from_file(glade_file)

        # Set defaults
        glade = etree.parse(glade_file)
        self.set_adjustment_values(builder,glade)

        # Populate the combo boxes
        combo = builder.get_object("sort_order_cb")
        self.set_model_from_list(combo,[
            'Complete one copy at a time (default)',
            'Best tracking (min vinyl movement)',
            'Fastest path (min blade movement)'])
        combo.set_active(0)

        # Connect the signals
        builder.connect_signals(self)
        self.widgets = self.keep_widgets(builder,[
            'main','smoothness','blade_offset','overcut','velocity',
            'force','feed_distance','req_copies','pos_x','pos_y',
            'spacing_row','spacing_col','material_w','material_l',
            'margin','weed_plot_padding','weed_copy_padding',
            'align_horizontal_box','align_vertical_box','weed_plot_box',
            'weed_copy_box','sort_order_box','invert_x_box',
            'invert_y_box','feed_to_origin_rad','statusbar','preview'
            ])

    def on_device_properties_activate(self,widget,data=None):
        self.app.ui['device_dialog'].widgets['main'].run()
        self.app.ui['device_dialog'].widgets['main'].hide()

    def on_job_open_activate(self,widget,data=None):
        """ Open a job """
        dialog = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN,
                    buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        dialog.set_current_folder(os.getenv('USERPROFILE') or os.getenv('HOME'))

        filter = gtk.FileFilter()
        filter.set_name("SVG Images")
        filter.add_mime_type("image/svg+xml")
        filter.add_pattern("*.svg")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("Plots")
        filter.add_pattern("*.hpgl")
        filter.add_pattern("*.gpgl")
        dialog.add_filter(filter)

        response = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            self.app.load(source_filename=filename)




class DeviceDialog(UserInterface):
    def __init__(self,app):
        """ Builds the device properties dialog window """
        self.app = app
        builder = gtk.Builder()
        glade_file = os.path.join(os.path.abspath(dirname(__file__)),'ui','device-dialog.glade')
        builder.add_from_file(glade_file)

        # Set defaults
        glade = etree.parse(glade_file)
        self.set_adjustment_values(builder,glade)

        # Populate the combo boxes
        # TODO: FIX FOR WINDOWS
        if os.name != 'nt':
            con = cups.Connection()
            printers = con.getPrinters()
            combo = builder.get_object("printer")
            self.set_model_from_list(combo,printers)
            combo.set_active(len(printers)-1)

        # Scan for serial ports, should work on both linux and windows
        ports = scan.scan()
        combo = builder.get_object("port")
        self.set_model_from_list(combo,ports)
        combo.set_active(len(ports)-1)

        combo = builder.get_object("baudrate")
        self.set_model_from_list(combo,[2400,4800,9600,19200,38400,57600,115200])
        combo.set_active(2)

        combo = builder.get_object("parity")
        self.set_model_from_list(combo,['None','Odd','Even','Mark','Space'])
        combo.set_active(0)

        combo = builder.get_object("stopbits")
        self.set_model_from_list(combo,[1,1.5,2])
        combo.set_active(0)

        combo = builder.get_object("bytesize")
        self.set_model_from_list(combo,[8,7,6,5])
        combo.set_active(0)

        # Connect the signals
        builder.connect_signals(self)

        self.widgets = self.keep_widgets(builder,[
            'main',
            ])

    def on_device_dialog_cancel_clicked(self,widget=None):
        """ Resets all the device settings then hides the dialog """
        self.widgets['main'].hide()

    def on_device_dialog_save_clicked(self,widget=None):
        """ Saves all the new device settings then hides the dialog """
        # database
        # session.commit()
        self.widgets['main'].hide()

    def delete_event(self,widget=None):
        """ cancel instead of destroying """
        self.on_device_dialog_cancel_clicked()
        return True
