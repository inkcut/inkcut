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
"""
This file serves two purposes, controlling the cutter progress and 
displaying the status.
"""
import time
import traceback
import serial
import os.path
from gi.repository import Gtk,GObject

from inkcut_lib.helpers import get_builder,get_media_file
import inkcut_lib.preferences as preferences
from inkcut_lib.device import Device
import inkcut_lib.filters  as filters

import gettext
from gettext import gettext as _
gettext.textdomain('inkcut')

import logging
logger = logging.getLogger('inkcut')

class StatusDialog(Gtk.Dialog):
    __gtype_name__ = "StatusDialog"

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated StatusDialog object.
        """
        builder = get_builder('StatusDialog')
        new_object = builder.get_object('status_dialog')
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called when we're finished initializing.

        finish_initalizing should be called after parsing the ui definition
        and creating a StatusDialog object with it in order to
        finish initializing the start of the new StatusDialog
        instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.toplevel = True
        self.ui = builder.get_ui(self)
        
        self.status = 'waiting' # ['running','paused','cancelled','finished','failed']
        self.stage = 0
        self.ui['flash'].set_label('Waiting for device...')
        self.ui['image1'].set_from_stock(Gtk.STOCK_GO_FORWARD,Gtk.IconSize.BUTTON)
        self.ui['btn_resume'].hide()
        self.ui['btn_ok'].hide()
        
    def plot(self,job,plugin=None,device=None):
		"""Controlls the process of converting a file and sending it to the device.
		Always updating the user with status changes.
		"""
		tasks = self.tasks(job,plugin,device)
		GObject.idle_add(tasks.next)
	
	def tasks(self,job,plugin,device):
		""" A generator that controls the process and displays
		the progress. 
		"""
        prefs = preferences.load()
        if device is None:
            device = Device(prefs['device'])
        self.device = device
		
		self.status = 'running'
		self.stage=1
		self.ui['image1'].set_from_stock(Gtk.STOCK_GO_FORWARD,Gtk.IconSize.BUTTON)
        if plugin=='inkscape':
            name = 'Inkscape Canvas'
        else:
            name = os.path.split(job)[1]
        self.ui['flash'].set_label('Converting %s to %s...'%(name,device.cmd_language))
        self.ui['progressbar'].set_fraction(0.1)
        yield True
        # TODO: Make this a generator with actual progress!
		converted_file = filters.convert(infile=job,preferences=prefs)
        self.ui['step1'].set_label('Finished processing data.')
        self.ui['flash'].set_label('Scheduling job on device queue...')
        self.ui['progressbar'].set_fraction(0.13)
        yield True

        device.schedule(converted_file)
		self.ui['progressbar'].set_fraction(0.14)
		self.ui['image1'].set_from_stock(Gtk.STOCK_APPLY,Gtk.IconSize.BUTTON)
		self.ui['image2'].set_from_stock(Gtk.STOCK_GO_FORWARD,Gtk.IconSize.BUTTON)
		yield True
		
		self.stage=2
		self.ui['flash'].set_label('Connecting to %s@%s...'%(device.name.replace(" ",""),device.serial_port))
		self.ui['progressbar'].set_fraction(0.15)
		yield True
		try:
			device.connect()
		except ValueError,e:
            self.ui['step2'].set_markup('<span color="#A52A2A" weight="bold">Could not setup a connection to the device.</span>\nAn invalid device configuration was given. Please try again, if the problem persists, contact the developer as this may be a bug.\n\n<span weight="bold">Details</span>\n%s'%e)
            self.ui['flash'].set_label('Error occurred...')
            self.ui['image2'].set_from_stock(Gtk.STOCK_DIALOG_ERROR,Gtk.IconSize.BUTTON)
            for item in ['step3','step4','image3','image4']:
                self.ui[item].hide()
            self.on_failure()
            yield False
            
		except serial.SerialException,e:
            self.ui['step2'].set_markup('<span color="#A52A2A" weight="bold">Could not setup a connection to the device.</span>\nPlease ensure that the device is connected and turned on and try again.\n\n<span weight="bold">Details</span>\n%s'%e)
            self.ui['flash'].set_label('Connection failed...')
            self.ui['image2'].set_from_stock(Gtk.STOCK_DIALOG_ERROR,Gtk.IconSize.BUTTON)
            for item in ['step3','step4','image3','image4']:
                self.ui[item].hide()
            self.on_failure()
            yield False
            
        self.ui['step2'].set_label('Connected to %s@%s.'%(device.name.replace(" ",""),device.serial_port))
		self.ui['progressbar'].set_fraction(0.2)
		yield True
		
		self.stage=3
		self.ui['flash'].set_label('Sending data...')
		self.ui['image2'].set_from_stock(Gtk.STOCK_APPLY,Gtk.IconSize.BUTTON)
		self.ui['image3'].set_from_stock(Gtk.STOCK_GO_FORWARD,Gtk.IconSize.BUTTON)
		self.ui['progressbar'].set_fraction(0.25)
		yield True
		try: 
			for task in device.execute():
				self.ui['progressbar'].set_fraction(0.25+device.status['fraction']*.65) # leave 10% for last step
				self.ui['flash'].set_label('Sending data... %s of %s (%i%%)'%(humanize_bytes(device.status['data_sent']),humanize_bytes(device.status['filesize']),int(device.status['fraction']*100)))
				if self.status == 'cancelled':
					self.ui['step4'].hide()
					self.ui['image4'].hide()
					self.ui['image3'].set_from_stock(Gtk.STOCK_STOP,Gtk.IconSize.BUTTON)
					self.ui['flash'].set_label('Cancelled...')
					yield False
				
				yield True
				
		except serial.SerialException,e:
            self.ui['step3'].set_markup('<span color="#A52A2A" weight="bold">Could complete sending data to the device.</span>\nPlease ensure that the device is connected and turned on and try again.\n\n<span weight="bold">Details</span>\n%s'%e)
            self.ui['flash'].set_label('Sending data failed...')
            self.ui['image3'].set_from_stock(Gtk.STOCK_DIALOG_ERROR,Gtk.IconSize.BUTTON)
            self.ui['step4'].hide()
            self.ui['image4'].hide()
            self.on_failure()
            yield False
        
        except:
			msg = Gtk.MessageDialog(type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format=_("An unexpected error occurred"))
            msg.format_secondary_text(_(traceback.format_exc()))
            msg.run()
            msg.destroy()
            self.ui['flash'].set_label('Sending data failed...')
            self.ui['image3'].set_from_stock(Gtk.STOCK_DIALOG_ERROR,Gtk.IconSize.BUTTON)
            self.ui['step4'].hide()
            self.ui['image4'].hide()
            self.on_failure()
            yield False
         
            
		self.ui['step3'].set_label('Data sent.')
		self.ui['flash'].set_label('Finializing...')
        os.remove(converted_file)
		self.ui['image3'].set_from_stock(Gtk.STOCK_APPLY,Gtk.IconSize.BUTTON)
		self.ui['image4'].set_from_stock(Gtk.STOCK_GO_FORWARD,Gtk.IconSize.BUTTON)
		self.ui['progressbar'].set_fraction(0.95)
		yield True
		
		"""
		"""
		self.stage=4
		device.disconnect()
		self.ui['step4'].set_label('Finalizing complete.')
		self.ui['flash'].set_label('')
		self.ui['image4'].set_from_stock(Gtk.STOCK_APPLY,Gtk.IconSize.BUTTON)
		self.ui['progressbar'].set_fraction(1)
		self.ui['btn_cancel'].hide()
		self.ui['btn_pause'].hide()
		self.ui['btn_resume'].hide()
		self.ui['btn_ok'].show()
		yield False

    def on_failure(self):
		self.ui['btn_cancel'].hide()
		self.ui['btn_pause'].hide()
		self.ui['btn_resume'].hide()
		self.ui['btn_ok'].show()
    
    def on_btn_pause_clicked(self, widget, data=None):
        self.pause = True
        widget.hide()
        self.device.status['state'] = "paused"
        self.ui["image%i"%self.stage].set_from_stock(Gtk.STOCK_MEDIA_PAUSE,Gtk.IconSize.BUTTON)
        self.ui['btn_resume'].show()
    
    def on_btn_resume_clicked(self, widget, data=None):
        self.pause = False
        widget.hide()
        self.device.status['state'] = "running"
        self.ui["image%i"%self.stage].set_from_stock(Gtk.STOCK_GO_FORWARD,Gtk.IconSize.BUTTON)
        self.ui['btn_pause'].show()

    def on_btn_cancel_clicked(self, widget, data=None):
		self.destroy()
    
    def on_btn_ok_clicked(self, widget, data=None):
		self.destroy()
    
    def on_destroy(self, widget, data=None):
		""" Disregard any unapplied changes and close the dialog."""
		if self.status == "running":
			self.status = "cancelled"
			self.device.status['state'] = "idle"
			Gtk.main_iteration()
        if self.toplevel:
            Gtk.main_quit()
        else:
            self.destroy()

def humanize_bytes(bytes, precision=1):
    """Return a humanized string representation of a number of bytes.
	Taken from http://code.activestate.com/recipes/577081-humanized-representation-of-a-number-of-bytes/
    Assumes `from __future__ import division`.

    >>> humanize_bytes(1)
    '1 byte'
    >>> humanize_bytes(1024)
    '1.0 kB'
    >>> humanize_bytes(1024*123)
    '123.0 kB'
    >>> humanize_bytes(1024*12342)
    '12.1 MB'
    >>> humanize_bytes(1024*12342,2)
    '12.05 MB'
    >>> humanize_bytes(1024*1234,2)
    '1.21 MB'
    >>> humanize_bytes(1024*1234*1111,2)
    '1.31 GB'
    >>> humanize_bytes(1024*1234*1111,1)
    '1.3 GB'
    """
    abbrevs = (
        (1<<50L, 'PB'),
        (1<<40L, 'TB'),
        (1<<30L, 'GB'),
        (1<<20L, 'MB'),
        (1<<10L, 'KB'),
        (1, 'bytes')
    )
    if bytes == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if bytes >= factor:
            break
    return '%.*f %s' % (precision, bytes / factor, suffix)

if __name__ == "__main__":
    dialog = StatusDialog()
    dialog.show()
    Gtk.main()
