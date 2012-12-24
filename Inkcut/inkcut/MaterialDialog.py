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

from gi.repository import Gtk, GObject, Gdk

import logging
logger = logging.getLogger('inkcut')

from inkcut_lib.helpers import InkcutDialog,get_builder, get_unit_model,get_combobox_active_text,set_model_from_list,read_unit,callback,get_unit_value
from inkcut_lib.material import DEFAULT_PROPERTIES
from inkcut_lib.preferences import UNITS

import gettext
from gettext import gettext as _
gettext.textdomain('inkcut')

class MaterialDialog(Gtk.Dialog,InkcutDialog):
    __gtype_name__ = "MaterialDialog"
    
    state_key = "material"

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated MaterialDialog object.
        """
        builder = get_builder('MaterialDialog')
        new_object = builder.get_object('material_dialog')
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called when we're finished initializing.

        finish_initalizing should be called after parsing the ui definition
        and creating a MaterialDialog object with it in order to
        finish initializing the start of the new MaterialDialog
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
        for id in ['cmb_media_width_units','cmb_media_length_units', 'cmb_margin_top_units','cmb_margin_left_units', 'cmb_margin_right_units','cmb_margin_bottom_units']:
            cmb = self.ui[id]
            cmb.set_model(length_units_model)
            cell = Gtk.CellRendererText()
            cmb.pack_start(cell,True)
            cmb.add_attribute(cell,'text',0)
            cmb.set_active(4) # 'in'
        
        # ================== Initialize General tab contents from saved or default state ============================
        self.ui['media_name'].set_text(self.state['current'][self.state_key]['name'])
        
        v,u = read_unit(self.state['current'][self.state_key]['width'])
        self.ui['adj_media_width'].set_value(v)
        self.ui['cmb_media_width_units'].set_active(u)
        
        v,u = read_unit(self.state['current'][self.state_key]['length'])
        self.ui['adj_media_length'].set_value(v)
        self.ui['cmb_media_length_units'].set_active(u)
        
        if self.state['current'][self.state_key]['is_roll']:
            self.ui['label_length'].hide()
            self.ui['sb_length'].hide()
            self.ui['cmb_media_length_units'].hide()
            self.ui['chk_media_is_roll'].set_active(True)  
        else:
            self.ui['chk_media_is_roll'].set_active(False)
        
        self.ui['media_color'].set_text(self.state['current'][self.state_key]['color'])
        
        color = Gdk.color_parse(self.state['current'][self.state_key]['color'])
        if color is not None:
            self.ui['btn_media_color'].set_color(color)
       
        # ================== Initialize Cutting tab contents from saved or default state ============================
        for item in ['margin_top','margin_left','margin_right','margin_bottom']:
            v,u = read_unit(self.state['current'][self.state_key]['%s'%item])
            self.ui['adj_%s'%item].set_value(v)
            self.ui['cmb_%s_units'%item].set_active(u)
        
        self.ui['chk_use_force'].set_active(self.state['current'][self.state_key]['use_cutting_force'])
        if not self.state['current'][self.state_key]['use_cutting_force']:
            self.ui['sc_force'].set_sensitive(False)
            self.ui['sb_force'].set_sensitive(False)
            self.ui['cmb_media_force_units'].set_sensitive(False)
        
        self.ui['chk_use_speed'].set_active(self.state['current'][self.state_key]['use_cutting_speed'])
        if not self.state['current'][self.state_key]['use_cutting_speed']:
            self.ui['sc_speed'].set_sensitive(False)
            self.ui['sb_speed'].set_sensitive(False)
            self.ui['cmb_media_speed_units'].set_sensitive(False)
        
        units = UNITS['force']
        v,u = read_unit(self.state['current'][self.state_key]['cutting_force'],units)
        self.ui['adj_cutting_force'].set_value(v)
        cmb = self.ui['cmb_media_force_units']
        set_model_from_list(cmb,units)
        cmb.set_active(u)
        
        units = UNITS['speed']
        v,u = read_unit(self.state['current'][self.state_key]['cutting_speed'],units)
        self.ui['adj_cutting_speed'].set_value(v)
        cmb = self.ui['cmb_media_speed_units']
        set_model_from_list(cmb,units)
        cmb.set_active(u)
        
        
        # ================== Initialize Accounting tab contents from saved or default state ============================
        units = UNITS['currency']
        v,u = read_unit(self.state['current'][self.state_key]['cost'],units)
        self.ui['adj_media_cost'].set_value(v)
        cmb = self.ui['cmb_media_cost_units']
        set_model_from_list(cmb,units)
        cmb.set_active(u)
        
        self.ui['fr_usage_history'].set_sensitive(False)
         
        # Final initialiation
        self.ui['btn_apply'].set_sensitive(False)
        self.unblock_all_handlers()
        
        
    #####################################################################################
    #                                   CALLBACKS                                        #
    #####################################################################################
    
    # =====================  General Tab Callbacks =============================
    @callback
    def on_media_name_changed(self,widget,data=None):
        if len(widget.get_text()):
            self.state['current'][self.state_key]['name'] = widget.get_text()
    
    @callback
    def on_adj_media_width_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_media_width'].get_value(),get_combobox_active_text(self.ui['cmb_media_width_units']))
        self.state['current'][self.state_key]['width'] = val
    
    @callback
    def on_cmb_media_width_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_media_width_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['width'],new_unit)
        self.ui['adj_media_width'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['width'] = val
        
    @callback
    def on_adj_media_length_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_media_length'].get_value(),get_combobox_active_text(self.ui['cmb_media_length_units']))
        self.state['current'][self.state_key]['length'] = val
        
    @callback
    def on_cmb_media_length_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_media_length_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['length'],new_unit)
        self.ui['adj_media_length'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['length'] = val
        
    @callback
    def on_chk_media_is_roll_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['is_roll'] = widget.get_active()
        if widget.get_active():
            self.ui['label_length'].hide()
            self.ui['sb_length'].hide()
            self.ui['cmb_media_length_units'].hide()
        else:
            self.ui['sb_length'].show()    
            self.ui['label_length'].show()
            self.ui['cmb_media_length_units'].show()
            
    @callback
    def on_btn_media_color_set(self,widget,data=None):
        c = widget.get_color().to_string()
        val = "#%s%s%s"%(c[1:3],c[5:7],c[9:11])
        self.state['current'][self.state_key]['color'] = val.upper()
        
        self.block_all_handlers()
        self.ui['media_color'].set_text(self.state['current'][self.state_key]['color'])
        self.unblock_all_handlers()
            
    @callback
    def on_media_color_changed(self,widget,data=None):
        val = widget.get_text()
        if val[0] == '#':
            if len(val) not in [4,7,10,13]:
                # not valid!
                return 0
            self.state['current'][self.state_key]['color'] = widget.get_text()
            color = Gdk.color_parse(self.state['current'][self.state_key]['color'])
            if color is not None:
                self.ui['btn_media_color'].set_color(color)
                
    # =====================  Cutting Tab Callbacks =============================
    @callback
    def on_adj_margin_top_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_margin_top'].get_value(),get_combobox_active_text(self.ui['cmb_margin_top_units']))
        self.state['current'][self.state_key]['margin_top'] = val
        
    @callback
    def on_cmb_margin_top_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_margin_top_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['margin_top'],new_unit)
        self.ui['adj_margin_top'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['margin_top'] = val
    
    @callback
    def on_adj_margin_left_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_margin_left'].get_value(),get_combobox_active_text(self.ui['cmb_margin_left_units']))
        self.state['current'][self.state_key]['margin_left'] = val
        
    @callback
    def on_cmb_margin_left_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_margin_left_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['margin_left'],new_unit)
        self.ui['adj_margin_left'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['margin_left'] = val
        
    @callback
    def on_adj_margin_right_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_margin_right'].get_value(),get_combobox_active_text(self.ui['cmb_margin_right_units']))
        self.state['current'][self.state_key]['margin_right'] = val
        
    @callback
    def on_cmb_margin_right_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_margin_right_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['margin_right'],new_unit)
        self.ui['adj_margin_right'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['margin_right'] = val
        
    @callback
    def on_adj_margin_bottom_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_margin_bottom'].get_value(),get_combobox_active_text(self.ui['cmb_margin_bottom_units']))
        self.state['current'][self.state_key]['margin_bottom'] = val
        
    @callback
    def on_cmb_margin_bottom_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_margin_bottom_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['margin_bottom'],new_unit)
        self.ui['adj_margin_bottom'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['margin_bottom'] = val
        
    @callback
    def on_chk_use_force_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['use_cutting_force'] = widget.get_active()
        self.ui['sc_force'].set_sensitive(widget.get_active())
        self.ui['sb_force'].set_sensitive(widget.get_active())
        self.ui['cmb_media_force_units'].set_sensitive(widget.get_active())
        
    @callback
    def on_chk_use_speed_toggled(self,widget,data=None):
        self.state['current'][self.state_key]['use_cutting_speed'] = widget.get_active()
        self.ui['sc_speed'].set_sensitive(widget.get_active())
        self.ui['sb_speed'].set_sensitive(widget.get_active())
        self.ui['cmb_media_speed_units'].set_sensitive(widget.get_active())
        
    @callback
    def on_adj_cutting_force_changed(self,widget,data=None):
        val = "%s%s"%(round(self.ui['adj_cutting_force'].get_value()/10.0)*10,get_combobox_active_text(self.ui['cmb_media_force_units']))
        self.state['current'][self.state_key]['cutting_force'] = val
        
    @callback
    def on_cmb_media_force_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_media_force_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['cutting_force'],new_unit,'force')
        self.ui['adj_cutting_force'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['cutting_force'] = val
        
    @callback
    def on_adj_cutting_speed_changed(self,widget,data=None):
        val = "%s%s"%(round(self.ui['adj_cutting_speed'].get_value()/4.0)*4,get_combobox_active_text(self.ui['cmb_media_speed_units']))
        self.state['current'][self.state_key]['cutting_speed'] = val
        
    @callback
    def on_cmb_media_speed_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_media_speed_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['cutting_speed'],new_unit,'speed')
        self.ui['adj_cutting_speed'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['cutting_speed'] = val
        
        
    # =====================  Accounting Tab Callbacks =============================
    @callback
    def on_adj_media_cost_changed(self,widget,data=None):
        val = "%s%s"%(self.ui['adj_media_cost'].get_value(),get_combobox_active_text(self.ui['cmb_media_cost_units']))
        self.state['current'][self.state_key]['cost'] = val
        
    @callback
    def on_cmb_media_cost_units_changed(self,widget,data=None):
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_media_cost_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current'][self.state_key]['cost'],new_unit,'currency')
        self.ui['adj_media_cost'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.unblock_all_handlers()
        self.state['current'][self.state_key]['cost'] = val
    
if __name__ == "__main__":
    dialog = MaterialDialog()
    dialog.show()
    Gtk.main()
