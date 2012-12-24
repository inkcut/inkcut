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
The purpose of this file is solely provide a UI to edit a copy of the 
DEFAULT_PROPERTIES dict defined in device.py.  This edited dict is used
in the inkcut app when converting and cutting files.
"""
from gi.repository import Gtk, GObject

import logging
logger = logging.getLogger('inkcut')

from inkcut import StatusDialog

from inkcut_lib.helpers import InkcutDialog,get_builder, get_unit_model,get_combobox_active_text,set_model_from_list,read_unit,callback,get_unit_value
from inkcut_lib.device import Device,DEFAULT_PROPERTIES,BAUDRATES,PARITY,BYTESIZE,STOPBITS,PACKET_SIZES,CURVE_QUALITY,CONNECTION_TYPES
from inkcut_lib.preferences import UNITS,TEST_FILE # using data/preferences.json

import gettext
from gettext import gettext as _
gettext.textdomain('inkcut')
    
def get_cmd_languages():
    return ['HPGL']
    
class DeviceDialog(Gtk.Dialog,InkcutDialog):
    __gtype_name__ = "DeviceDialog"
    
    state_key = "device"

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated DeviceDialog object.
        """
        builder = get_builder('DeviceDialog')
        new_object = builder.get_object('device_dialog')
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called when we're finished initializing.

        finish_initalizing should be called after parsing the ui definition
        and creating a DeviceDialog object with it in order to
        finish initializing the start of the new DeviceDialog
        instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self)
        self.toplevel = True # Set this to false if you want it to run like a dialog
        
        self.load_state(DEFAULT_PROPERTIES)
        self.block_all_handlers() # prevent callbacks from being called when loading values
        
        # Initialize all of the unit comboboxes
        length_units_model = get_unit_model()
        for id in ['cmb_device_width_units','cmb_device_length_units', 'cmb_device_laser_x_units','cmb_device_laser_y_units', 'cmb_device_x_calibration_units','cmb_device_y_calibration_units','cmb_device_blade_offset_units','cmb_device_path_overcut_units']:
            cmb = self.ui[id]
            cmb.set_model(length_units_model)
            cell = Gtk.CellRendererText()
            cmb.pack_start(cell,True)
            cmb.add_attribute(cell,'text',0)
            cmb.set_active(4) # 'in'
        
        # ================== Initialize General tab contents from saved or default state ============================
        self.ui['device_name'].set_text(self.state['current'][self.state_key]['name'])
        
        v,u = read_unit(self.state['current'][self.state_key]['width'])
        self.ui['adj_device_width'].set_value(v)
        self.ui['cmb_device_width_units'].set_active(u)
        
        v,u = read_unit(self.state['current'][self.state_key]['length'])
        self.ui['adj_device_length'].set_value(v)
        self.ui['cmb_device_length_units'].set_active(u)
        
        self.ui['chk_device_uses_roll'].set_active(self.state['current'][self.state_key]['uses_roll'])
        if self.state['current'][self.state_key]['uses_roll']:
            self.ui['label_length'].hide()
            self.ui['sb_length'].hide()
            self.ui['cmb_device_length_units'].hide()
            self.ui['chk_device_uses_roll'].set_active(True)    
            
        self.ui['chk_device_rotation'].set_active(self.state['current'][self.state_key]['rotation'])
        self.ui['img_device_rotation'].set_from_stock(self.state['current'][self.state_key]['rotation'] and Gtk.STOCK_GO_FORWARD or Gtk.STOCK_GO_DOWN,Gtk.IconSize.BUTTON)
        
        self.ui['chk_use_force'].set_active(self.state['current'][self.state_key]['use_cutting_force'])
        if not self.state['current'][self.state_key]['use_cutting_force']:
            self.ui['sc_force'].set_sensitive(False)
            self.ui['sb_force'].set_sensitive(False)
            self.ui['cmb_device_force_units'].set_sensitive(False)
        
        self.ui['chk_use_speed'].set_active(self.state['current'][self.state_key]['use_cutting_speed'])
        if not self.state['current'][self.state_key]['use_cutting_speed']:
            self.ui['sc_speed'].set_sensitive(False)
            self.ui['sb_speed'].set_sensitive(False)
            self.ui['cmb_device_speed_units'].set_sensitive(False)
        
        units = UNITS['force']
        v,u = read_unit(self.state['current'][self.state_key]['cutting_force'],units)
        self.ui['adj_device_force'].set_value(v)
        cmb = self.ui['cmb_device_force_units']
        set_model_from_list(cmb,units)
        cmb.set_active(u)
        
        units = UNITS['speed']
        v,u = read_unit(self.state['current'][self.state_key]['cutting_speed'],units)
        self.ui['adj_device_speed'].set_value(v)
        cmb = self.ui['cmb_device_speed_units']
        set_model_from_list(cmb,units)
        cmb.set_active(u)
        # Completed 10/29/2011 - 1:03 PM ET - Jairus Martin - (C) Vinylmark LLC
        
        # ================== Initialize Connection tab contents from saved or default state  ============================
        #self.ui['cmb_device_serial_port'].connect('popup',self.on_cmb_device_serial_port_popdown)
        cmb = self.ui['cmb_device_conn_type']
        set_model_from_list(cmb,CONNECTION_TYPES)
        try:
            cmb.set_active(CONNECTION_TYPES.index(self.state['current'][self.state_key]['connection_type']))
        except ValueError:
            cmb.set_active(self.state['default'][self.state_key]['connection_type'])
        
        self.connection_page_reload()
        
        self.cmb_device_printers_rescan(self.ui['cmb_device_printers'])
        
        self.cmb_device_serial_port_rescan(self.ui['cmb_device_serial_port'])
        
        units = [str(rate) for rate in BAUDRATES]
        cmb = self.ui['cmb_device_serial_baudrate']
        set_model_from_list(cmb,units)
        try: 
            u = units.index(str(self.state['current'][self.state_key]['serial_baudrate']))
        except ValueError:    
            u = units.index(str(self.state['default'][self.state_key]['serial_baudrate']))
        cmb.set_active(u)
        
        units = PARITY
        cmb = self.ui['cmb_device_serial_parity']
        set_model_from_list(cmb,units)
        try: 
            u = units.index(str(self.state['current'][self.state_key]['serial_parity']))
        except ValueError:
            u = units.index(str(self.state['default'][self.state_key]['serial_parity']))
        cmb.set_active(u)
        
        units = STOPBITS
        cmb = self.ui['cmb_device_serial_stopbits']
        set_model_from_list(cmb,units)
        try:
            u = units.index(self.state['current'][self.state_key]['serial_stopbits'])
        except ValueError:
            u = units.index(self.state['default'][self.state_key]['serial_stopbits'])
        cmb.set_active(u)
        
        units = BYTESIZE
        cmb = self.ui['cmb_device_serial_bytesize']
        set_model_from_list(cmb,units)
        try:
            u = units.index(self.state['current'][self.state_key]['serial_bytesize'])
        except ValueError:
            u = units.index(self.state['default'][self.state_key]['serial_bytesize'])
        cmb.set_active(u)
        
        self.ui['chk_device_serial_xonxoff'].set_active(self.state['current'][self.state_key]['serial_xonxoff'])
        self.ui['chk_device_serial_rtscts'].set_active(self.state['current'][self.state_key]['serial_rtscts'])
        self.ui['chk_device_serial_dsrdtr'].set_active(self.state['current'][self.state_key]['serial_dsrdtr'])
        
        
        units = PACKET_SIZES
        v,u = read_unit(self.state['current'][self.state_key]['data_packet_size'],units)
        self.ui['adj_device_packet_size'].set_value(v)
        cmb = self.ui['cmb_device_packet_size_units']
        set_model_from_list(cmb,units)
        cmb.set_active(u)
        
        # ================== Initialize Registration tab contents from saved or default state  ============================
        
        self.ui['page_registration'].set_sensitive(False)

        # ================== Initialize Advanced tab contents from saved or default state  ============================        
        units = CURVE_QUALITY
        cmb = self.ui['cmb_device_curve_quality']
        set_model_from_list(cmb,units)
        try: 
            u = units.index(self.state['current'][self.state_key]['curve_quality'])
        except ValueError:
            u = units.index(self.state['default'][self.state_key]['curve_quality'])
        cmb.set_active(u)
        
        v,u = read_unit(self.state['current'][self.state_key]['blade_offset'])
        self.ui['adj_device_blade_offset'].set_value(v)
        self.ui['cmb_device_blade_offset_units'].set_active(u)
        
        v,u = read_unit(self.state['current'][self.state_key]['path_overcut'])
        self.ui['adj_device_path_overcut'].set_value(v)
        self.ui['cmb_device_path_overcut_units'].set_active(u)
        
        units = get_cmd_languages()
        cmb = self.ui['cmb_device_command_language']
        set_model_from_list(cmb,units)
        try:
            u = units.index(self.state['current'][self.state_key]['cmd_language'])
        except ValueError:
            u = units.index(self.state['default'][self.state_key]['cmd_language'])
        cmb.set_active(u)
        
        self.ui['chk_device_cmds_before'].set_active(self.state['current'][self.state_key]['use_cmd_before'])
        self.ui['entry_device_cmds_before'].set_text(self.state['current'][self.state_key]['cmd_before'])
        if not self.state['current'][self.state_key]['use_cmd_before']:
            self.ui['entry_device_cmds_before'].set_sensitive(False)
        
        self.ui['chk_device_cmds_after'].set_active(self.state['current'][self.state_key]['use_cmd_after'])
        self.ui['entry_device_cmds_after'].set_text(self.state['current'][self.state_key]['cmd_after'])
        if not self.state['current'][self.state_key]['use_cmd_after']:
            self.ui['entry_device_cmds_after'].set_sensitive(False)    
            
        units = ['steps/in']
        v,u = read_unit(self.state['current'][self.state_key]['resolution'],units)
        self.ui['adj_device_resolution'].set_value(v)
        cmb = self.ui['cmb_device_resolution_units']
        set_model_from_list(cmb,units)
        cmb.set_active(u)
        # ================== end of Advanced tab ============================
        
        # Final initialiation
        self.ui['btn_apply'].set_sensitive(False)
        self.unblock_all_handlers()
        
    # end of finish_initializing()
    
    #####################################################################################
    #                                   CALLBACKS                                        #
    #####################################################################################
    
    # =====================  General Tab Callbacks =============================
    @callback
    def on_device_name_changed(self,widget,data=None):
        if len(widget.get_text()):
            self.state['current'][self.state_key]['name'] = widget.get_text()
    
    @callback
    def on_adj_device_width_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_device_width'].get_value(),get_combobox_active_text(self.ui['cmb_device_width_units']))
        self.state['current'][self.state_key]['width'] = val
        
    @callback
    def on_cmb_device_width_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_width_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['width'],new_unit)
        self.ui['adj_device_width'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['width'] = val

    @callback
    def on_adj_device_length_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_device_length'].get_value(),get_combobox_active_text(self.ui['cmb_device_length_units']))
        self.state['current'][self.state_key]['length'] = val
        
    @callback
    def on_cmb_device_length_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_length_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['length'],new_unit)
        self.ui['adj_device_length'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['length'] = val

    @callback
    def on_chk_device_uses_roll_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['uses_roll'] = widget.get_active()
        if widget.get_active():
            self.ui['label_length'].hide()
            self.ui['sb_length'].hide()
            self.ui['cmb_device_length_units'].hide()
        else:
            self.ui['sb_length'].show()    
            self.ui['label_length'].show()
            self.ui['cmb_device_length_units'].show()
    
    @callback
    def on_chk_device_rotation_toggled(self,widget,data=None):
        """ Note: False means 0 deg rotation, True means 90 deg"""
        self.state['current'][self.state_key]['rotation'] = widget.get_active()
        if widget.get_active():
            self.ui['img_device_rotation'].set_from_stock(Gtk.STOCK_GO_FORWARD,Gtk.IconSize.BUTTON)
        else:
            self.ui['img_device_rotation'].set_from_stock(Gtk.STOCK_GO_DOWN,Gtk.IconSize.BUTTON)

    @callback
    def on_chk_use_force_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['use_cutting_force'] = widget.get_active()
        self.ui['sc_force'].set_sensitive(widget.get_active())
        self.ui['sb_force'].set_sensitive(widget.get_active())
        self.ui['cmb_device_force_units'].set_sensitive(widget.get_active())
        
    @callback
    def on_chk_use_speed_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['use_cutting_speed'] = widget.get_active()
        self.ui['sc_speed'].set_sensitive(widget.get_active())
        self.ui['sb_speed'].set_sensitive(widget.get_active())
        self.ui['cmb_device_speed_units'].set_sensitive(widget.get_active())
        
    @callback
    def on_adj_device_force_changed(self,widget,data=None):
        val = round(self.ui['adj_device_force'].get_value()/10.0)*10
        self.ui['adj_device_force'].set_value(val)# snap to ticks, this will send another callback (if val%10 !==0) so it occurs twice
        val = "%s%s"%(int(val),get_combobox_active_text(self.ui['cmb_device_force_units']))
        self.state['current'][self.state_key]['cutting_force'] = val
        
    @callback
    def on_cmb_device_force_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_force_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['cutting_force'],new_unit,'force')
        self.ui['adj_device_force'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['cutting_force'] = val
    
    @callback
    def on_adj_device_speed_changed(self,widget,data=None):
        val = round(self.ui['adj_device_speed'].get_value()/4.0)*4
        self.ui['adj_device_speed'].set_value(val)# snap to ticks, this will send another callback (if val%4 !==0) so it occurs twice
        val = "%s%s"%(int(val),get_combobox_active_text(self.ui['cmb_device_speed_units']))
        self.state['current'][self.state_key]['cutting_speed'] = val
        
    @callback
    def on_cmb_device_speed_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_speed_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['cutting_speed'],new_unit,'speed')
        self.ui['adj_device_speed'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['cutting_speed'] = val
        
    @callback
    def on_chk_device_use_material_settings_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['use_material_settings'] = widget.get_active()
    # Completed 10/29/2011 - 1:02 PM ET - Jairus Martin - (C) Vinylmark LLC
    
    # ===================== Connection Tab Callbacks =============================
    @callback
    def on_cmb_device_conn_type_changed(self,widget,data=None):
        self.state['current'][self.state_key]['connection_type'] = get_combobox_active_text(widget)
        self.connection_page_reload()
        
    def connection_page_reload(self):
        if self.state['current'][self.state_key]['connection_type'] == CONNECTION_TYPES[1]: # Printer
            #show printer settings
            self.ui['fr_com_port'].hide()
            self.ui['fr_com_settings'].hide()
            self.ui['fr_com_packet_size'].hide()
            self.ui['fr_printer'].show()
        else:
            #show serial settings
            self.ui['fr_printer'].hide()
            self.ui['fr_com_port'].show()
            self.ui['fr_com_settings'].show()
            self.ui['fr_com_packet_size'].show()
    
    def cmb_device_printers_rescan(self,widget,data=None):
        """ Scan for new ports each time it the rescan button is clicked"""
        results = Device.get_printers()
        if len(results):
            self.ui['msg_printer_box'].hide()
            set_model_from_list(widget,results)
            u = 0
            try:
                for i in range(0,len(results)):
                    if results[i] == self.state['current'][self.state_key]['printer_name']:
                        u = i
            except KeyError:
                pass
            widget.set_active(u)
        else:
            set_model_from_list(widget,[])
            self.ui['msg_printer_box'].show()
    
    def cmb_device_serial_port_rescan(self,widget,data=None):
        """ Scan for new ports each time it is popped down """
        ports = Device.get_serial_ports()
        if len(ports):
            self.ui['msg_port_box'].hide()
            set_model_from_list(widget,ports)
            u = 0
            for i in range(0,len(ports)):
                if ports[i] == self.state['current'][self.state_key]['serial_port']:
                    u = i
            widget.set_active(u)
        else:
            set_model_from_list(widget,[]) # Make it empty!
            self.ui['msg_port_box'].show()
            
    @callback        
    def on_cmb_device_printers_changed(self,widget,data=None):
        self.state['current'][self.state_key]['printer_name'] = get_combobox_active_text(widget)

    @callback        
    def on_cmb_device_serial_port_changed(self,widget,data=None):
        self.state['current'][self.state_key]['serial_port'] = get_combobox_active_text(widget)
    
    @callback        
    def on_cmb_device_serial_baudrate_changed(self,widget,data=None):
        self.state['current'][self.state_key]['serial_baudrate'] = int(get_combobox_active_text(widget))
    
    @callback        
    def on_cmb_device_serial_bytesize_changed(self,widget,data=None):
        self.state['current'][self.state_key]['serial_bytesize'] = get_combobox_active_text(widget)
    
    @callback        
    def on_cmb_device_serial_parity_changed(self,widget,data=None):
        self.state['current'][self.state_key]['serial_parity'] = get_combobox_active_text(widget)
    
    @callback        
    def on_cmb_device_serial_stopbits_changed(self,widget,data=None):
        self.state['current'][self.state_key]['serial_stopbits'] = get_combobox_active_text(widget)
    
    @callback
    def on_chk_device_serial_xonxoff_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['serial_xonxoff'] = widget.get_active()    
    
    @callback
    def on_chk_device_serial_rtscts_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['serial_rtscts'] = widget.get_active()    
    
    @callback
    def on_chk_device_serial_dsrdtr_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['serial_dsrdtr'] = widget.get_active()    
    
    @callback
    def on_adj_device_packet_size_changed(self,widget,data=None):
        val = "%s%s"%(int(self.ui['adj_device_packet_size'].get_value()),get_combobox_active_text(self.ui['cmb_device_packet_size_units']))
        self.state['current'][self.state_key]['data_packet_size'] = val
        
    @callback
    def on_cmb_device_packet_size_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_packet_size_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['data_packet_size'],new_unit,'filesize')
        self.ui['adj_device_packet_size'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['data_packet_size'] = val
    
    @callback
    def on_btn_rescan_devices_clicked(self,widget,data=None):
        """ Rescans the correct type of device based on connectino_type setting """
        if self.state['current'][self.state_key]['connection_type'] == CONNECTION_TYPES[1]: # Printer
            self.cmb_device_printers_rescan(self.ui['cmb_device_printers'])
        else:
            self.cmb_device_serial_port_rescan(self.ui['cmb_device_serial_port'])            
        
    @callback
    def on_btn_test_connection_clicked(self,widget,data=None):
        """ Attempts to send test data to the device using the current settings """
        GObject.idle_add(self.run_test_cut)
        
    def run_test_cut(self):
        """ Attempts to send test data to the device using the current settings """
        device = Device(self.state['current'][self.state_key])
        dialog = StatusDialog.StatusDialog()
        dialog.toplevel = False
        dialog.set_title("Test Connection - Inkcut")
        dialog.plot(TEST_FILE,device=device)
        dialog.show()
        
    
    # ===================== Registration tab callbacks =============================                
    @callback
    def on_adj_device_laser_x_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_device_laser_x'].get_value(),get_combobox_active_text(self.ui['cmb_device_laser_x_units']))
        self.state['current'][self.state_key]['laser_x_offset'] = val
        
    @callback
    def on_cmb_device_laser_x_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_laser_x_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['laser_x_offset'],new_unit)
        self.ui['adj_device_laser_x'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['laser_x_offset'] = val       

    @callback
    def on_adj_device_laser_y_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_device_laser_y'].get_value(),get_combobox_active_text(self.ui['cmb_device_laser_y_units']))
        self.state['current'][self.state_key]['laser_y_offset'] = val
        
    @callback
    def on_cmb_device_laser_y_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_laser_y_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['laser_y_offset'],new_unit)
        self.ui['adj_device_laser_y'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['laser_y_offset'] = val
    
    def on_btn_laser_calibrate_clicked(self,widget,data=None):
        # TODO: open laser calibration dialog
        pass
    
    def on_btn_output_calibrate_clicked(self,widget,data=None):
        # TODO: cut a calibration rectangle and prompt user to measure it
        pass
    
    @callback
    def on_adj_device_x_calibration_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_device_x_calibration'].get_value(),get_combobox_active_text(self.ui['cmb_device_x_calibration_units']))
        self.state['current'][self.state_key]['long_edge_cal'] = val    
        
    @callback
    def on_cmb_device_x_calibration_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_x_calibration_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['long_edge_cal'],new_unit)
        self.ui['adj_device_x_calibration'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['long_edge_cal'] = val 
    
    @callback
    def on_adj_device_y_calibration_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_device_y_calibration'].get_value(),get_combobox_active_text(self.ui['cmb_device_y_calibration_units']))
        self.state['current'][self.state_key]['short_edge_cal'] = val   
        
    @callback
    def on_cmb_device_y_calibration_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_y_calibration_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['short_edge_cal'],new_unit)
        self.ui['adj_device_y_calibration'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['short_edge_cal'] = val 
        
    # ===================== Advanced Tab Callbacks =============================    
    @callback        
    def on_cmb_device_curve_quality_changed(self,widget,data=None):
        self.state['current'][self.state_key]['curve_quality'] = get_combobox_active_text(widget)
    
    @callback
    def on_adj_device_blade_offset_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_device_blade_offset'].get_value(),get_combobox_active_text(self.ui['cmb_device_blade_offset_units']))
        self.state['current'][self.state_key]['blade_offset'] = val  
        
    @callback
    def on_cmb_device_blade_offset_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_blade_offset_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['blade_offset'],new_unit)
        self.ui['adj_device_blade_offset'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['blade_offset'] = val   
    
    @callback
    def on_adj_device_path_overcut_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_device_path_overcut'].get_value(),get_combobox_active_text(self.ui['cmb_device_path_overcut_units']))
        self.state['current'][self.state_key]['path_overcut'] = val
        
    @callback
    def on_cmb_device_path_overcut_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_path_overcut_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['path_overcut'],new_unit)
        self.ui['adj_device_path_overcut'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['path_overcut'] = val 
    
    @callback        
    def on_cmb_device_command_language_changed(self,widget,data=None):
        self.state['current'][self.state_key]['cmd_language'] = get_combobox_active_text(widget)
        
    @callback
    def on_chk_device_cmds_before_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['use_cmd_before'] = widget.get_active()
        self.ui['entry_device_cmds_before'].set_sensitive(widget.get_active())
    
    @callback
    def on_entry_device_cmds_before_changed(self,widget,data=None):
        self.state['current'][self.state_key]['cmd_before'] = widget.get_text()
    
    @callback
    def on_chk_device_cmds_after_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['use_cmd_after'] = widget.get_active()
        self.ui['entry_device_cmds_after'].set_sensitive(widget.get_active())
        
    @callback
    def on_entry_device_cmds_after_changed(self,widget,data=None):
        self.state['current'][self.state_key]['cmd_after'] = widget.get_text()
    
    @callback
    def on_adj_device_resolution_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_device_resolution'].get_value(),get_combobox_active_text(self.ui['cmb_device_resolution_units']))
        self.state['current'][self.state_key]['resolution'] = val    
    
    @callback
    def on_cmb_device_resolution_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_device_resolution_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['resolution'],new_unit)
        self.ui['adj_device_resolution'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['resolution'] = val 

if __name__ == "__main__":
    dialog = DeviceDialog()
    dialog.run()
    dialog.destroy()
