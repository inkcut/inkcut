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

import gettext
from gettext import gettext as _
gettext.textdomain('inkcut')

from gi.repository import Gtk,GObject,GdkPixbuf
import traceback
import logging
logger = logging.getLogger('inkcut')


import tempfile
import os
from lxml import etree
import rsvg

from inkcut_lib.helpers import get_builder, get_unit_model,get_unit_value,get_combobox_active_text,set_model_from_list,read_unit,callback
from inkcut_lib import Window, Plot 
from inkcut_lib.device import Device
from inkcut_lib.plot import CUTTING_ORDERS as PLOT_ORDERS
from inkcut_lib.preferences import PLUGIN_EXTENSIONS,DRAWING_MODES,PREVIEWING_MODES,GRAPHIC_ROTATIONS
from inkcut_lib.preferences import APP_PREFERENCES,PLOT_PROPERTIES

from inkcut.StatusDialog import StatusDialog
from inkcut.DeviceDialog import DeviceDialog
from inkcut.MaterialDialog import MaterialDialog
from inkcut.AboutInkcutDialog import AboutInkcutDialog
#from inkcut.PreferencesInkcutDialog import PreferencesInkcutDialog

# See inkcut_lib.Window.py for more details about how this class works
class InkcutWindow(Window):
    __gtype_name__ = "InkcutWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(InkcutWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutInkcutDialog
        self.DeviceDialog = DeviceDialog
        self.MaterialDialog = MaterialDialog
        self.StatusDialog = StatusDialog

        self.plot = None
        self.preview = None
        self.load_state(PLOT_PROPERTIES,load_all=True)
        self.on_graphic_changed(initialize=True)
        self.preview_file = None
        self.cutter_file = None
        
    def on_act_zoom_in_activate(self,widget=None,data=None):
        if self.plot is None:
            return
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.preview_file.name)
        if pixbuf is not None:
            # Determine the original scale
            w = self.ui['preview_window'].get_allocated_width()-15
            scale = w/float(self.plot.get_material_width())
            h = scale*pixbuf.get_height()
            
            # Determine the new scale
            z = self.state['global']['app']['zoom']*1.25
            self.state['global']['app']['zoom'] = z
            
            scaled_buf = pixbuf.scale_simple(round(w*z),round(h*z),GdkPixbuf.InterpType.BILINEAR)
            self.ui['img_preview'].set_from_pixbuf(scaled_buf)
            
    def on_act_zoom_out_activate(self,widget=None,data=None):
        if self.plot is None:
            return
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.preview_file.name)
        if pixbuf is not None:
            # Determine the original scale
            w = self.ui['preview_window'].get_allocated_width()-15
            scale = w/float(self.plot.get_material_width())
            h = scale*pixbuf.get_height()
            
            # Determine the new scale
            z = self.state['global']['app']['zoom']*0.75
            self.state['global']['app']['zoom'] = z
            
            scaled_buf = pixbuf.scale_simple(round(w*z),round(h*z),GdkPixbuf.InterpType.BILINEAR)
            self.ui['img_preview'].set_from_pixbuf(scaled_buf)
            
    def on_act_zoom_restore_activate(self,widget=None,data=None):
        if self.plot is None:
            return
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.preview_file.name)
        if pixbuf is not None:
            # Determine the original scale
            w = self.ui['preview_window'].get_allocated_width()-15
            scale = w/float(self.plot.get_material_width())
            h = scale*pixbuf.get_height()
            
            # Determine the new scale
            self.state['global']['app']['zoom'] = 1
            
            scaled_buf = pixbuf.scale_simple(w,h,GdkPixbuf.InterpType.BILINEAR)
            self.ui['img_preview'].set_from_pixbuf(scaled_buf)
    
    def update_preview(self):
        # See https://wiki.edubuntu.org/UbuntuOpportunisticDeveloperWeek/GooCanvas
        if self.plot is None:
            return
        
        # Add the new preview image
        if self.state['global']['app']['drawing_mode']=="svg":
            try:
                os.remove(self.preview_file.name)
            except:
                pass
            self.preview_file = tempfile.NamedTemporaryFile(suffix=".svg",delete=False)
            self.preview_file.file.write(self.plot.get_preview_xml())
            self.preview_file.file.close()
            self.ui['img_preview'].hide()
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.preview_file.name)
            
            # Scale it so the whole plot fits in the window
            w = self.ui['preview_window'].get_allocated_width()-15
            scale = w/float(self.plot.get_material_width())
            h = scale*pixbuf.get_height()
            self.state['global']['app']['zoom'] = 1
            scaled_buf = pixbuf.scale_simple(w,h,GdkPixbuf.InterpType.BILINEAR)
            self.ui['img_preview'].set_from_pixbuf(scaled_buf)
            self.ui['img_preview'].show()
            """
            # Remove the previous preview image it it exists
            try:
                self.preview.remove()
            except:
                pass
            pb = Pixbuf.new_from_file(tmp.name)
            cont_left, cont_top, cont_right, cont_bottom = self.ui['canvas'].get_bounds()
            img_w = pb.get_width(); img_h = pb.get_height(); img_left = (cont_right - img_w)/2; img_top = (cont_bottom - img_h)/2
            self.preview = goocanvas.Image(pixbuf=pb,parent=self.ui['canvas'].get_root_item(), x=img_left,y=img_top)
            """
        self.flash("")
        return False
    #####################################################################################
    #                                   CALLBACKS                                       #
    #####################################################################################
    # ================== file menu action items =========================
    @callback(False)
    def on_mnu_open_activate(self,widget,data=None):
        """
        Displays a file chooser dialog. When a file is selected, a new
        job is created using the file.
        """
        dialog = Gtk.FileChooserDialog(title=_('Open File - Inkcut'),action=Gtk.FileChooserAction.OPEN,
                    buttons=(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN,Gtk.ResponseType.OK))
        last_folder = self.state['global']['app'].get('last_file_open_dir') or os.getenv('USERPROFILE') or os.getenv('HOME')
        dialog.set_current_folder(last_folder)

        filter = Gtk.FileFilter()
        filter.set_name(_("SVG files"))
        filter.add_mime_type("image/svg+xml")
        filter.add_pattern("*.svg")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name(_("All files"))
        filter.add_pattern("*")
        dialog.add_filter(filter)

        # Todo, set these from plugins
        filter = Gtk.FileFilter()
        filter.set_name(_("Plot files"))
        for pattern in PLUGIN_EXTENSIONS:
            filter.add_pattern(pattern)
        dialog.add_filter(filter)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            last_folder = os.path.abspath(os.path.dirname(filename))
            self.state['global']['app']['last_file_open_dir'] = last_folder
            logger.debug("Set last_file_open_dir = %s"%last_folder)
            msg = "Opening file: %s..."%filename
            self.flash(msg,indicator=True)
            GObject.idle_add(self.open_plot_from_file,filename)
            
        dialog.destroy()
            
    def open_plot_from_file(self,filename,data=None):
        w = get_unit_value(self.state['global']['material']['width'])
        h = None
        if not self.state['global']['material']['is_roll']:
            h = get_unit_value(self.state['global']['material']['length'])
        try:
            # TODO: RUN IMPORT PLUGIN HERE ==================================
            # TODO: RUN IMPORT PLUGIN HERE ==================================
            self.plot = Plot(w,h,self.state['global']['material']['color'])
            self.plot.set_padding(top=get_unit_value(self.state['global']['material']['margin_top']), 
                                  right=get_unit_value(self.state['global']['material']['margin_right']), 
                                  bottom=get_unit_value(self.state['global']['material']['margin_bottom']),
                                  left=get_unit_value(self.state['global']['material']['margin_left']))
            self.plot.set_graphic(filename)
            self.on_graphic_changed()
            self.update_preview()
            name = os.path.basename(filename)
            msg = '%s opened'%name
            self.set_title("*%s - Inkcut"%name)
            self.flash(msg)
        except:
            msg = Gtk.MessageDialog(type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format=_("Could not open file: %s"%(filename)))
            msg.format_secondary_text(_(traceback.format_exc()))
            msg.run()
            msg.destroy()
            self.flash("Could not open file...")
            return False
        return False
    
    # =================== CALLBACKS ============================================
    def on_graphic_changed(self,use_saved_state=False,initialize=False):
        """Reset everything to defaults. If use_saved_state, load the plot
        settings from the 'saved' state. If initalize is set, it will ignore
        w,h and populate comboboxes. 
        """
        source = use_saved_state and 'saved' or 'default' 
        self.block_all_handlers()
        if initialize:
            # Populate all the combo boxes
            set_model_from_list(self.ui['cmb_plot_order'],PLOT_ORDERS)
            set_model_from_list(self.ui['cmb_graphic_rotation'],GRAPHIC_ROTATIONS)
            set_model_from_list(self.ui['cmb_plot_order'],PLOT_ORDERS)
            # Initialize all of the unit comboboxes
            length_units_model = get_unit_model()
            for id in ['cmb_graphic_width_units','cmb_graphic_height_units', 'cmb_graphic_spacing_x_units','cmb_graphic_spacing_y_units', 'cmb_plot_position_x_units','cmb_plot_position_y_units','cmb_plot_feed_distance_units']:
                cmb = self.ui[id]
                cmb.set_model(length_units_model)
                cell = Gtk.CellRendererText()
                cmb.pack_start(cell,True)
                cmb.add_attribute(cell,'text',0)
                cmb.set_active(4) # 'in'
                
            w,h = 0,0
        if self.plot:
            properties = self.plot.get_properties()
            # Read the dimensions and convert the value to the current units
            self._update_graphic_size()
            self.ui['chk_graphic_scale_lock'].set_active(self.state[source]['plot']['graphic_scale_lock'])
            self.ui['adj_graphic_copies'].set_value(self.plot.get_copies())
            
            try: 
                u = int(round(self.plot.graphic.get_rotation()/90.0))
            except ValueError:    
                u = GRAPHIC_ROTATIONS.index(str(self.state['default']['plot']['graphic_rotation']))
            self.ui['cmb_graphic_rotation'].set_active(u)
            
            #self.ui['chk_graphic_auto_rotate'].set_active(self.state[source]['plot']['graphic_auto_rotate'])
            self.ui['chk_graphic_auto_rotate'].set_active(self.plot.get_auto_rotate())
            
            v,u = read_unit(self.state[source]['plot']['graphic_spacing_x'])
            self.ui['cmb_graphic_spacing_x_units'].set_active(u)
            v = get_unit_value('%spx'%self.plot.get_spacing()[0],get_combobox_active_text(self.ui['cmb_graphic_spacing_x_units']))
            self.ui['adj_graphic_spacing_x'].set_value(v)
            
            v,u = read_unit(self.state[source]['plot']['graphic_spacing_y'])
            self.ui['cmb_graphic_spacing_y_units'].set_active(u)
            v = get_unit_value('%spx'%self.plot.get_spacing()[1],get_combobox_active_text(self.ui['cmb_graphic_spacing_y_units']))
            self.ui['adj_graphic_spacing_y'].set_value(v)
            
            # Second tab
            self.ui['chk_graphic_mirror_x'].set_active(self.plot.get_mirror_x_status())
            self.ui['chk_graphic_mirror_y'].set_active(self.plot.get_mirror_y_status())
            
            self.ui['chk_plot_center_x'].set_active(self.plot.get_align_center_x_status())
            if self.state[source]['plot']['plot_center_x']:
                self.ui['box_plot_position_x'].hide()
            v,u = read_unit(self.state[source]['plot']['graphic_spacing_x'])
            self.ui['cmb_plot_position_x_units'].set_active(u)
            v = get_unit_value('%spx'%self.plot.get_position()[0],get_combobox_active_text(self.ui['cmb_plot_position_x_units']))
            self.ui['adj_plot_position_x'].set_value(v)
            
            self.ui['chk_plot_center_y'].set_active(self.plot.get_align_center_y_status())
            if self.state['global']['material']['is_roll']:
                self.ui['chk_plot_center_y'].hide()
            if self.state[source]['plot']['plot_center_y']:
                self.ui['box_plot_position_y'].hide()
            v,u = read_unit(self.state[source]['plot']['graphic_spacing_x'])
            self.ui['cmb_plot_position_y_units'].set_active(u)
            v = get_unit_value('%spx'%self.plot.get_position()[1],get_combobox_active_text(self.ui['cmb_plot_position_y_units']))
            self.ui['adj_plot_position_y'].set_value(v)
            
            
            self.ui['rb_return_to_origin'].set_active(self.plot.get_finish_position() == (0,0))
            v,u = read_unit(self.state[source]['plot']['plot_feed_distance'])
            self.ui['adj_plot_feed_distance'].set_value(v)
            self.ui['cmb_plot_feed_distance_units'].set_active(u)
            
            try: 
                u = PLOT_ORDERS.index(self.plot.get_cutting_order())
            except ValueError:    
                u = PLOT_ORDERS.index(str(self.state['default']['plot']['plot_order']))
            self.ui['cmb_plot_order'].set_active(u)
            
            #self.ui['chk_plot_weedline'].set_active(self.state[source]['plot']['plot_weedline'])
            self.ui['chk_plot_weedline'].set_active(self.plot.get_weedline_status())
            
            #self.ui['chk_graphic_weedline'].set_active(self.state[source]['plot']['graphic_weedline'])
            self.ui['chk_graphic_weedline'].set_active(self.plot.graphic.get_weedline_status())
        self.unblock_all_handlers()
        self.on_chk_graphic_scale_lock_toggled(self.ui['chk_graphic_scale_lock'])
        
    def _update_graphic_size(self):
        w = get_unit_value('%spx'%self.plot.graphic.get_width(),get_combobox_active_text(self.ui['cmb_graphic_width_units'])) 
        h = get_unit_value('%spx'%self.plot.graphic.get_height(),get_combobox_active_text(self.ui['cmb_graphic_height_units']))
        self.block_all_handlers()
        self.ui['adj_graphic_width'].set_value(w)
        self.ui['adj_graphic_height'].set_value(h)
        sx,sy = self.plot.graphic.get_scale()
        self.ui['adj_graphic_scale_x'].set_value(sx*100)
        self.ui['adj_graphic_scale_y'].set_value(sy*100)
        self.unblock_all_handlers()
    
    @callback
    def on_adj_graphic_copies_value_changed(self,adjustment,data=None):
        """Set's the plot's copies to the adjustment value. """
        n = int(adjustment.get_value())
        #self.state['current']['plot']['graphic_copies'] = n
        self.flash("Setting the number of copies to %s..."%n,indicator=True)
        self.state['current']['plot']['graphic_copies'] = n
        GObject.idle_add(self.plot.set_copies,n)
        GObject.idle_add(self.update_preview)
        
    @callback
    def on_btn_add_stack_activate(self,button, data=None):
        """Adds a full stack of copies"""
        stack = self.plot.get_stack_size_x()
        copies = self.plot.get_copies()
        self.ui['adj_graphic_copies'].set_value(stack*(copies/stack+1))
        # Preview updated by on_plot_copies_changed
        
    @callback
    def on_btn_remove_stack_activate(self,button, data=None):
        """Sets the graphic-copies to 1"""
        stack = self.plot.get_stack_size_x()
        copies = self.plot.get_copies()
        if ((copies-stack)>1):
            self.ui['adj_graphic_copies'].set_value(copies-stack)
        # Preview updated by on_plot_copies_changed
        
    @callback
    def on_btn_clear_copies_activate(self,button, data=None):
        """Sets the graphic-copies to 1"""
        self.ui['adj_graphic_copies'].set_value(1)
        # Preview updated by on_plot_copies_changed
        
    @callback
    def on_cmb_graphic_rotation_changed(self, combobox, data=None):
        degrees = combobox.get_active()*90
        self.flash("Setting graphic rotation to %s..."%degrees,indicator=True)
        self.state['current']['plot']['graphic_rotation'] = get_combobox_active_text(self.ui['cmb_graphic_rotation'])
        GObject.idle_add(self.plot.graphic.set_rotation,degrees)
        GObject.idle_add(self._update_graphic_size)
        GObject.idle_add(self.update_preview)
    
    @callback
    def on_adj_graphic_spacing_x_value_changed(self,adjustment,data=None):
        val = "%s%s"%(self.ui['adj_graphic_spacing_x'].get_value(),get_combobox_active_text(self.ui['cmb_graphic_spacing_x_units']))
        self.state['current']['plot']['graphic_spacing_x'] = val
        x = get_unit_value(val)
        if self.plot and self.plot.get_copies() > 1:
            msg = "Updating the column spacing..."
        else:
            msg = "Saving the plot column spacing..."
        
        self.flash(msg,indicator=True)
        GObject.idle_add(self.plot.set_spacing,x,None)
        GObject.idle_add(self.update_preview)
        
    @callback
    def on_cmb_graphic_spacing_x_units_changed(self,widget,data=None):
        """This should not update the plot as the px value is the same!"""
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_graphic_spacing_x_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current']['plot']['graphic_spacing_x'],new_unit)
        self.ui['adj_graphic_spacing_x'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.state['current']['plot']['graphic_spacing_x'] = val
        self.unblock_all_handlers()

    @callback
    def on_adj_graphic_spacing_y_value_changed(self,adjustment,data=None):
        val = "%s%s"%(self.ui['adj_graphic_spacing_y'].get_value(),get_combobox_active_text(self.ui['cmb_graphic_spacing_y_units']))
        self.state['current']['plot']['graphic_spacing_y'] = val
        y = get_unit_value(val)
        
        if self.plot and (self.plot.get_copies() > self.plot.get_stack_size_x()):
            msg = "Updating the row spacing..."
        else:
            msg = "Saving the plot row spacing..."
        
        self.flash(msg,indicator=True)
        GObject.idle_add(self.plot.set_spacing,None,y)
        GObject.idle_add(self.update_preview)
        
    @callback
    def on_cmb_graphic_spacing_y_units_changed(self,widget,data=None):
        """This should not update the plot as the px value is the same!"""
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_graphic_spacing_y_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.state['current']['plot']['graphic_spacing_y'],new_unit)
        self.ui['adj_graphic_spacing_y'].set_value(new_val)
        val = "%s%s"%(new_val,new_unit)
        self.state['current']['plot']['graphic_spacing_y'] = val
        self.unblock_all_handlers()

    @callback
    def on_plot_position_x_changed(self,widget,data=None):
        x = self.unit_to(widget.get_value())
        pos = self.plot.get_position()
        self.flash("Moving the plot to (%s,%s)"%(x,pos[1]),indicator=True)
        GObject.idle_add(self.plot.set_position,x,pos[1])
        GObject.idle_add(self.update_preview)

    @callback
    def on_plot_position_y_changed(self,widget,data=None):
        y = self.unit_to(widget.get_value())
        pos = self.plot.get_position()
        self.flash("Moving the plot to (%s,%s)"%(pos[0],y),indicator=True)
        GObject.idle_add(self.plot.set_position,pos[0],y)
        GObject.idle_add(self.update_preview)

    @callback
    def on_chk_plot_weedline_toggled(self,checkbox,data=None):
        enabled = checkbox.get_active()
        if enabled:
            msg = "Adding a weedline to the plot..."
        else:
            msg = "Removing the plot weedline..."
        self.state['current']['plot']['plot_weedline'] = enabled
        self.flash(msg,indicator=True)
        GObject.idle_add(self.plot.set_weedline,enabled)
        GObject.idle_add(self.update_preview)

    @callback
    def on_plot_weedline_padding_changed(self,adjustment,data=None):
        if self.get_widget('plot-properties','plot-weedline-enable').get_active():
            msg = "Updating the plot weedline padding..."
        else:
            msg = "Saving the plot weedline padding..."
        self.flash(msg,indicator=True)
        GObject.idle_add(self.plot.set_weedline_padding,self.unit_to(adjustment.get_value()))
        GObject.idle_add(self.update_preview)
    
    # ===================================== Graphic Callbacks ===============================================
    @callback
    def on_adj_graphic_width_value_changed(self,adjustment,data=None):
        # Calculate new scale
        cur = self.plot.graphic.get_width()
        val = '%s%s'%(self.ui['adj_graphic_width'].get_value(),get_combobox_active_text(self.ui['cmb_graphic_width_units']))
        new = float(get_unit_value(val))
        sx,sy = self.plot.graphic.get_scale()
        s = new/cur*sx
        GObject.idle_add(self.ui['adj_graphic_scale_x'].set_value,s*100)
        
    @callback
    def on_cmb_graphic_width_units_changed(self,widget,data=None):
        """This should not update the plot as the px value is the same!"""
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_graphic_width_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.plot.graphic.get_width(),new_unit)
        self.ui['adj_graphic_width'].set_value(new_val)
        #TODO Save units used to app here
        self.unblock_all_handlers()
        
    @callback
    def on_adj_graphic_height_value_changed(self,adjustment,data=None):
        # Calculate new scale
        cur = self.plot.graphic.get_height()
        val = '%s%s'%(self.ui['adj_graphic_height'].get_value(),get_combobox_active_text(self.ui['cmb_graphic_height_units']))
        new = float(get_unit_value(val))
        sx,sy = self.plot.graphic.get_scale()
        s = new/cur*sy
        GObject.idle_add(self.ui['adj_graphic_scale_y'].set_value,s*100)
        
    @callback
    def on_cmb_graphic_height_units_changed(self,widget,data=None):
        """This should not update the plot as the px value is the same!"""
        self.block_all_handlers() # So we don't call the callback when setting to the new value
        new_unit = get_combobox_active_text(self.ui['cmb_graphic_height_units'])
        # Convert value to equivalent value in new units
        new_val = get_unit_value(self.plot.graphic.get_height(),new_unit)
        self.ui['adj_graphic_height'].set_value(new_val)
        #TODO Save units used to app here
        self.unblock_all_handlers()
        
    def _refresh_graphic_size_adjustments(self):
        w = get_unit_value('%spx'%self.plot.graphic.get_width(),get_combobox_active_text(self.ui['cmb_graphic_width_units'])) 
        h = get_unit_value('%spx'%self.plot.graphic.get_height(),get_combobox_active_text(self.ui['cmb_graphic_height_units']))
        self.block_all_handlers()
        self.ui['adj_graphic_width'].set_value(w)
        self.ui['adj_graphic_height'].set_value(h)
        self.unblock_all_handlers()
        
    @callback
    def on_adj_graphic_scale_x_value_changed(self,adjustment,data=None):
        sx = self.ui['adj_graphic_scale_x'].get_value()/100.0
        self.state['current']['plot']['graphic_scale_x'] = sx
        if self.state['current']['plot']['graphic_scale_lock']:
            sy = sx
            self.state['current']['plot']['graphic_scale_y'] = sy
        else:
            sy = self.state['current']['plot']['graphic_scale_y']
        GObject.idle_add(self.plot.graphic.set_scale,sx,sy)
        GObject.idle_add(self._refresh_graphic_size_adjustments)
        GObject.idle_add(self.update_preview)
    
    @callback
    def on_adj_graphic_scale_y_value_changed(self,adjustment,data=None):
        sy = self.ui['adj_graphic_scale_y'].get_value()/100.0
        self.state['current']['plot']['graphic_scale_y'] = sy
        if self.state['current']['plot']['graphic_scale_lock']:
            sx = sy
            self.state['current']['plot']['graphic_scale_x'] = sx
        else:
            sx = self.state['current']['plot']['graphic_scale_x']
        GObject.idle_add(self.plot.graphic.set_scale,sx,sy)
        GObject.idle_add(self._refresh_graphic_size_adjustments)
        GObject.idle_add(self.update_preview)
        
    @callback
    def on_chk_graphic_scale_lock_toggled(self,widget,data=None):
        active = self.ui['chk_graphic_scale_lock'].get_active()
        self.state['current']['plot']['graphic_scale_lock'] = active
        
        was_blocked = self._block_callbacks 
        self.block_all_handlers()
        if active:
            self.ui['sb_scale_x'].set_tooltip_text("Set the scale of the graphic")
            self.ui['sb_scale_y'].hide()
            self.ui['lb_scale_y'].hide()
            self.ui['adj_graphic_scale_y'].set_value(100*self.state['current']['plot']['graphic_scale_x'])
        else:
            self.ui['sb_scale_x'].set_tooltip_text("Set the scale of the horizontal axis")
            self.ui['sb_scale_y'].show()
            self.ui['lb_scale_y'].show()
            self.ui['adj_graphic_scale_y'].set_value(100*self.state['current']['plot']['graphic_scale_y'])
        
        if not was_blocked: self.unblock_all_handlers()
    
    @callback
    def on_graphic_rotate_to_save_toggled(self,checkbox,data=None):
        self.flash("Checking and updating...",indicator=True)
        self.state['current']['plot']['graphic_auto_rotate'] = checkbox.get_active()
        GObject.idle_add(self.plot.set_auto_rotate,checkbox.get_active())
        GObject.idle_add(self.update_preview)
        
    @callback
    def on_graphic_weedline_padding_changed(self,adjustment,data=None):
        if self.get_widget('graphic-properties','graphic-weedline-enable').get_active():
            msg = "Updating the graphic weedline padding..."
        else:
            msg = "Saving the graphic weedline padding..."
        self.flash(msg,indicator=True)
        GObject.idle_add(self.plot.graphic.set_weedline_padding,self.unit_to(adjustment.get_value()))
        GObject.idle_add(self._update_graphic_ui)
        
    @callback
    def on_chk_graphic_weedline_toggled(self,checkbox,data=None):
        enabled = checkbox.get_active()
        if enabled:
            msg = "Adding a weedline to the graphic..."
        else:
            msg = "Removing the graphic weedline..."
        self.state['current']['plot']['graphic_weedline'] = enabled
        self.flash(msg,indicator=True)
        GObject.idle_add(self.plot.graphic.set_weedline,enabled)
        GObject.idle_add(self.update_preview)
        
    @callback
    def on_chk_graphic_mirror_x_toggled(self,checkbox,data=None):
        enabled = checkbox.get_active()
        if enabled:
            msg = "Mirroring graphic about the x-axis..."
        else:
            msg = "Returning graphic to original mirror state..."
        self.state['current']['plot']['graphic_mirror_x'] = enabled
        self.flash(msg,indicator=True)
        GObject.idle_add(self.plot.graphic.set_mirror_x,enabled)
        GObject.idle_add(self.update_preview)

    @callback
    def on_chk_graphic_mirror_y_toggled(self,checkbox,data=None):
        enabled = checkbox.get_active()
        if enabled:
            msg = "Mirroring graphic about the y-axis..."
        else:
            msg = "Returning graphic to original mirror state..."
        self.state['current']['plot']['graphic_mirror_y'] = enabled
        self.flash(msg,indicator=True)
        GObject.idle_add(self.plot.graphic.set_mirror_y,enabled)
        GObject.idle_add(self.update_preview)
        

    @callback
    def on_mnu_save_activate(self,widget,data=None):
        # Save the file
        pass
    
    @callback
    def on_mnu_save_as_activate(self,widget,data=None):
        # Save the file
        pass

    @callback
    def on_mnu_print_activate(self,widget,data=None):
        # Display the cut dialog
        try:
            os.remove(self.cutter_file.name)
            logger.info('Cutter file removed.')
        except:
            pass
        logger.info('Creating new cutter file...')
        self.cutter_file = tempfile.NamedTemporaryFile(delete=False)
        self.cutter_file.file.write(self.plot.get_xml())
        self.cutter_file.file.close()
        logger.info('Cutter file saved.')
        
        device = Device(self.state['global']['device'])
        dialog = self.StatusDialog()
        dialog.toplevel = False
        dialog.set_title("Cutting Status - Inkcut")
        dialog.plot(self.cutter_file.name,device=device)
        dialog.show()
    
    @callback
    def on_mnu_print_preview_activate(self,widget,data=None):
        # Open the plot SVG file with Inkscape
        self.context.finish()

    # ================== view menu action items =========================
    
    # ========================== Toolbar callbacks ==========================
    @callback
    def on_chk_plot_center_x_toggled(self,widget,data=None):
        active = self.ui['chk_plot_center_x'].get_active()
        self.state['current']['plot']['plot_center_x'] = active
        if active:
            msg = "Centering the plot horizontally..."
            self.ui['box_plot_position_x'].hide()
        else:
            msg = "Moving the plot to the horizontal start..."
            self.ui['box_plot_position_x'].show()
        self.flash(msg,indicator=True)
        GObject.idle_add(self.plot.set_align_center_x,active)
        GObject.idle_add(self.update_preview)
        
    @callback
    def on_chk_plot_center_y_toggled(self,widget,data=None):
        active = self.ui['chk_plot_center_y'].get_active()
        self.state['current']['plot']['plot_center_y'] = active
        if active:
            self.ui['box_plot_position_y'].hide()
            msg = "Centering the plot vertically..."
        else:
            self.ui['box_plot_position_y'].show()
            msg = "Moving the plot to the vertical start..."
        self.flash(msg,indicator=True)
        GObject.idle_add(self.plot.set_align_center_y,active)
        GObject.idle_add(self.update_preview)
    
    #TODO: the Dialog should emit a signal when apply is clicked
    @callback
    def on_material_updated(self):
        if self.plot and (self.state['global']['material'] != self.material_dialog.state['saved']):
            w = get_unit_value(self.material_dialog.state['saved']['material']['width'])
            h = None
            if not self.material_dialog.state['saved']['material']['is_roll']:
                h = get_unit_value(self.material_dialog.state['saved']['material']['length'])
            c = self.material_dialog.state['saved']['material']['color']
            if self.material_dialog.state['saved']['material']['is_roll']:
                self.ui['chk_plot_center_y'].hide()
            else:
                self.ui['chk_plot_center_y'].show()
            GObject.idle_add(self.plot.set_material,w,h,c)
            GObject.idle_add(self.plot.set_padding,
                                get_unit_value(self.state['global']['material']['margin_top']), 
                                get_unit_value(self.state['global']['material']['margin_right']), 
                                get_unit_value(self.state['global']['material']['margin_bottom']),
                                get_unit_value(self.state['global']['material']['margin_left'])
                            )
            GObject.idle_add(self.update_preview)
            
    def on_material_dialog_destroyed(self, widget, data=None):
        """Update the plot with the new values (if any)"""
        self.on_material_updated()
        super(InkcutWindow, self).on_material_dialog_destroyed(widget,data)
        
    def on_destroy(self, widget, data=None):
        try:
            os.remove(self.preview_file.name)
            logger.info('Preview file removed.')
        except:
            pass
        try:
            os.remove(self.cutter_file.name)
            logger.info('Cutter file removed.')
        except:
            pass
        super(InkcutWindow, self).on_destroy(widget,data)
        
    # ======================== A little UI jazz =============================
    def flash(self,msg,duration=5,context_id=None,indicator=False):
        """ Flash a message in the statusbar for duration in s"""
        #self.indicator(indicator)
        logger.info(msg)
        if duration>0:
            GObject.timeout_add(duration*1000,self.flash,"",0)
            
        statusbar = self.ui['statusbar']
        if context_id is None:
            context_id = statusbar.get_context_id(_(msg))
        statusbar.push(context_id,msg)
        return 0
    """
    def indicator(self,enabled=True):
        spinner = self.ui['spinner']
        if enabled:
            spinner.show()
            return 0
        else:
            spinner.hide()
            return 0
    """
