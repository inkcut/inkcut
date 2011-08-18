#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# App: Inkcut
# File: inkcut.py
# Author: Copyright 2011 Jairus Martin <frmdstryr@gmail.com>
# Date: 15 Aug 2011
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

import sys
import os

# Path Globals
APP_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(APP_DIR,'lib'))

import logging,logging.config
import pygtk
pygtk.require('2.0')
import gtk
import ConfigParser
import tempfile


# Inkcut modules
from meta import Session
from job import Job
from material import Material
from device import Device
from lxml import etree
from sqlalchemy import create_engine

# Load Configuration Files
config = ConfigParser.RawConfigParser()
CONFIG_FILE = os.path.join(APP_DIR,'conf','app.cfg')
config.read(CONFIG_FILE)

# Logging
logging.config.fileConfig(CONFIG_FILE)
log = logging.getLogger("inkcut")


class Application(object):
    """
    Inkcut application, handles gui and device/job interaction
    """

    def __init__(self):
        """Load initial application settings from database """
        # setup the database session
        engine = create_engine('sqlite:///%s'%os.path.join(APP_DIR,config.get('Inkcut','database_dir'),config.get('Inkcut','database_name')))

        Session.configure(bind=engine)
        self.session = Session()

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
        # Check if similar job exists
        jobs = self.session.query(Job).filter(Job.source_filename == unicode(source_filename)).all()
        if len(jobs)==0:
            job = Job(source=source,source_filename=source_filename,selected_nodes=selected_nodes)
            job.material = self.session.query(Material).first()
            if job.load():
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
        else:
            # open a new job or
            msg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                buttons=gtk.BUTTONS_CLOSE,
                message_format='A similar job was already found, do you want to load that?')
            msg.set_title('File Already Found opening file')
            msg.run()
            msg.destroy()
            return False

    def reload_device(self):
        """ Reloads the device """
        pass

    def reload_job(self):
        """ Refreshes the current job """
        if self.ui['main_window'].widgets['live_preview'].get_active():
            self._update_preview()

    def _update_preview(self):
        """ Refreshes the preview """
        loader = gtk.gdk.PixbufLoader('svg')
        data = self.job.get_preview_svg()
        loader.write(data)
        loader.close()
        pixbuf = loader.get_pixbuf()
        w = float(pixbuf.get_width())
        h = float(pixbuf.get_height())
        # fix for dynamic height!
        height = 480;
        pixbuf = pixbuf.scale_simple(int(w*height/h),height,gtk.gdk.INTERP_BILINEAR)
        self.ui['main_window'].widgets['preview'].set_from_pixbuf(pixbuf)

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
        glade_file = os.path.join(APP_DIR,'ui','main-window.glade')
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

        combo = builder.get_object("copy_rotation")
        self.set_model_from_list(combo,['%s°'%(i*90) for i in range(0,4)])
        combo.set_active(0)

        materials = app.session.query(Material).all()
        combo = builder.get_object("material_select")
        self.set_model_from_list(combo,[m.name for m in materials])
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
            'invert_y_box','feed_to_origin_rad','statusbar','preview',
            'copy_rotation_img','live_preview'
            ])

    # Job actions
    def on_material_select_changed(self,combo,data=None):
        """ Update the job's material """
        self.app.job.reload_job()


    def on_material_color_btn_color_set(self,button,data=None):
        """ Update the material's color and preview """
        self.app.reload_job()


    def on_copy_rotation_changed(self,combo,data=None):
        """ Update the job's data rotation """
        self.app.reload_job()


    # Menu actions
    def on_job_open_activate(self,widget,data=None):
        """ Open a job """
        dialog = gtk.FileChooserDialog(title='Open File - Inkcut',action=gtk.FILE_CHOOSER_ACTION_OPEN,
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

    def on_preview_refresh_activate(self,widget,data=None):
        """ Manually refresh the preview """
        self.app._update_preview()

    def on_refresh_job_preview_activate(self,widget,data=None):
        pass

    def on_submit_job_activate(self,widget,data=None):
        pass

    def on_cut_clicked(self,widget,data=None):
        pass

    def on_preview_clicked(self,widget,data=None):
        pass

    def on_live_preview_toggled(self,widget,data=None):
        pass

    def on_send_clicked(self,widget,data=None):
        self.app.job.submit()

    def on_pause_clicked(self,widget,data=None):
        pass

    def on_invertbox_toggled(self,widget,data=None):
        self.app.job.requirements.set_mirror(True)

    def on_material_size_changed(self,widget,data=None):
        pass

    def on_margin_value_changed(self,widget,data=None):
        pass

    def on_spacing_value_changed(self,widget,data=None):
        pass

    def on_pos_value_changed(self,widget,data=None):
        pass

    def on_copies_value_changed(self,widget,data=None):
        pass

    def on_feeding_group_changed(self,widget,data=None):
        pass

    def on_force_value_changed(self,widget,data=None):
        pass

    def on_velocity_value_changed(self,widget,data=None):
        pass

    def on_overcut_value_changed(self,widget,data=None):
        pass

    def on_offset_value_changed(self,widget,data=None):
        pass

    def on_smoothness_value_changed(self,widget,data=None):
        pass

    def on_margin_value_changed(self,widget,data=None):
        pass

    def on_margin_value_changed(self,widget,data=None):
        pass

    def on_stack_btn_clicked(self,widget,data=None):
        pass

    def on_reset_stack_btn_clicked(self,widget,data=None):
        pass

    def on_weed_box_toggled(self,widget,data=None):
        pass

    def on_weed_v_box_toggled(self,widget,data=None):
        pass

    def on_order_changed(self,widget,data=None):
        pass

    def on_reset_stack_btn_clicked(self,widget,data=None):
        pass

    def on_test_connection_clicked(self,widget,data=None):
        pass


    # Dialogs this window controls
    def on_device_properties_activate(self,widget,data=None):
        self.app.ui['device_dialog'].widgets['main'].run()
        self.app.ui['device_dialog'].widgets['main'].hide()

    def on_material_properties_activate(self,widget,data=None):
        #self.app.ui['device_dialog'].widgets['main'].run()
        #self.app.ui['device_dialog'].widgets['main'].hide()
        pass

    def on_inkcut_preferences_activate(self,widget,data=None):
        #self.app.ui['device_dialog'].widgets['main'].run()
        #self.app.ui['device_dialog'].widgets['main'].hide()
        pass

    def open_about_dialog(self,widget,data=None):
        #self.app.ui['device_dialog'].widgets['main'].run()
        #self.app.ui['device_dialog'].widgets['main'].hide()
        pass


class DeviceDialog(UserInterface):
    def __init__(self,app):
        """ Builds the device properties dialog window """
        self.app = app
        builder = gtk.Builder()
        glade_file = os.path.join(APP_DIR,'ui','device-dialog.glade')
        builder.add_from_file(glade_file)

        # Set defaults
        glade = etree.parse(glade_file)
        self.set_adjustment_values(builder,glade)

        # Populate the combo boxes
        # TODO: FIX FOR WINDOWS
        #if os.name != 'nt':
        #    con = cups.Connection()
        #    printers = con.getPrinters()
        #    combo = builder.get_object("printer")
        #    self.set_model_from_list(combo,printers)
        #    combo.set_active(len(printers)-1)

        # Scan for serial ports, should work on both linux and windows
        ports = Device.port_scan()
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

if __name__ == "__main__":
    app = Application()
    #etree.parse(sys.stdin), sys.argv[1:]

    #sys.stdin.close()
    app.run()

