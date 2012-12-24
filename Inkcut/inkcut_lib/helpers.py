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

"""Helpers for an Ubuntu application."""
import logging
import os
import re
import geom.inkex
import platform 

from gi.repository import Gtk # pylint: disable=E0611

from . inkcutconfig import get_data_file
from . Builder import Builder

import preferences

import json
import logging
logger = logging.getLogger('inkcut')


import gettext
from gettext import gettext as _
gettext.textdomain('inkcut')

def get_builder(builder_file_name):
    """Return a fully-instantiated Gtk.Builder instance from specified ui 
    file
    
    :param builder_file_name: The name of the builder file, without extension.
        Assumed to be in the 'ui' directory under the data path.
    """
    # Look for the ui file that describes the user interface.
    ui_filename = get_data_file('ui', '%s.ui' % (builder_file_name,))
    if not os.path.exists(ui_filename):
        ui_filename = None

    builder = Builder()
    builder.set_translation_domain('inkcut')
    builder.add_from_file(ui_filename)
    return builder


# Owais Lone : To get quick access to icons and stuff.
def get_media_file(media_file_name):
    media_filename = get_data_file('media', '%s' % (media_file_name,))
    if not os.path.exists(media_filename):
        media_filename = None

    return "file:///"+media_filename

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

def set_up_logging(opts):
    # add a handler to prevent basicConfig
    root = logging.getLogger()
    null_handler = NullHandler()
    root.addHandler(null_handler)

    formatter = logging.Formatter("%(levelname)s:%(name)s: %(funcName)s() '%(message)s'")

    logger = logging.getLogger('inkcut')
    logger_sh = logging.StreamHandler()
    logger_sh.setFormatter(formatter)
    logger.addHandler(logger_sh)

    lib_logger = logging.getLogger('inkcut_lib')
    lib_logger_sh = logging.StreamHandler()
    lib_logger_sh.setFormatter(formatter)
    lib_logger.addHandler(lib_logger_sh)

    # Set the logging level to show debug messages.
    if opts.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('logging enabled')
    if opts.verbose > 1:
        lib_logger.setLevel(logging.DEBUG)

def get_help_uri(page=None):
    # help_uri from source tree - default language
    here = os.path.dirname(__file__)
    help_uri = os.path.abspath(os.path.join(here, '..', 'help', 'C'))

    if not os.path.exists(help_uri):
        # installed so use gnome help tree - user's language
        help_uri = 'inkcut'

    # unspecified page is the index.page
    if page is not None:
        help_uri = '%s#%s' % (help_uri, page)

    return help_uri

def show_uri(parent, link):
    screen = parent.get_screen()
    Gtk.show_uri(screen, link, Gtk.get_current_event_time())

def alias(alternative_function_name):
    '''see http://www.drdobbs.com/web-development/184406073#l9'''
    def decorator(function):
        '''attach alternative_function_name(s) to function'''
        if not hasattr(function, 'aliases'):
            function.aliases = []
        function.aliases.append(alternative_function_name)
        return function
    return decorator

# lxml shortcut functions, should be pushed into a different file!
def get_element_by_id(etreeElement, id):
    """Returns the first etree element with the given id"""
    assert type(etreeElement) == inkex.etree.Element, "etreeElement must be an etree.Element!"
    path = '//*[@id="%s"]' % id
    el_list = etreeElement.xpath(path, namespaces=inkex.NSS)
    if el_list:
      return el_list[0]
    else:
      return None

def get_selected_nodes(etreeElement,id_list):
    """Returns a list of nodes that have an id in the id_list."""
    assert type(etreeElement) in [inkex.etree._ElementTree,inkex.etree.Element], "etreeElement must be an etree.Element!"
    assert type(id_list) == list, "id_list must be a list of id's to search for"
    nodes = []
    for id in id_list:
        path = '//*[@id="%s"]' % id
        for node in etreeElement.xpath(path, namespaces=inkex.NSS):
            nodes.append(node)
    return nodes
    

def get_combobox_active_text(combobox):
   model = combobox.get_model()
   active = combobox.get_active()
   if active < 0:
      return None
   return model[active][0]

def set_model_from_list (cb, items):
    """Setup a ComboBox or ComboBoxEntry based on a list of strings."""
    model = Gtk.ListStore(str)
    for item in items:
        model.append([item])
    cb.set_model(model)
    if type(cb) == Gtk.ComboBoxText:
        cb.set_text_column(0)
    elif type(cb) == Gtk.ComboBox:
        cb.clear() # Remove old items
        cell =  Gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        



#a dictionary of unit to user unit conversion factors
# Taken from inkex.py from inkscape: Copyright (C) 2005,2007 Aaron Spike, aaron@ekips.org
# ==============================================================================================
uuconv = preferences.UNITS['length']
""" 
uuconv = {'cm':35.433070866, 'ft':1080, 'in':90.0, 'km':3543307.0866,'pc':15.0,  
        'pt':1.25, 'px':1, 'm':3543.3070866,'mm':3.5433070866, 'yd':3240}
 """
def unittouu(string,units=uuconv):
    '''Returns userunits given a string representation of units in another system'''
    unit = re.compile('(%s)$' % '|'.join(units.keys()))
    param = re.compile(r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')

    p = param.match(string)
    u = unit.search(string)    
    if p:
        retval = float(p.string[p.start():p.end()])
    else:
        retval = 0.0
    if u:
        try:
            return retval * units[u.string[u.start():u.end()]]
        except KeyError:
            pass
    return retval

def uutounit(val, unit):
    return val/uuconv[unit]
    
# ==============================================================================================


def read_unit(string,units=uuconv.keys(),val=0,unit_index=0):
    """Splits a string with units into a tuple of (val,units.index(unit)). Based on unittouu.
    This is designed to be used with a Gtk liststore.
    """
    if type(units) is dict:
        unit = re.compile('(%s)$' % '|'.join(units.keys()))
    elif type(units) is list:
        unit = re.compile('(%s)$' % '|'.join(units))
        
    param = re.compile(r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')

    p = param.match(string)
    u = unit.search(string)  
    if p:
        retval = float(p.string[p.start():p.end()])
    else:
        retval = val

    retindex = unit_index
    if u:
        try: 
            retindex = units.index(u.string[u.start():u.end()])
        except:
            pass
    return (retval,retindex)

def get_unit_value(string,unit="px",unit_type='length'):
    """
    gets_unit_value using several overloading methods:
    
    If unit is a dict containing unit conversion values:
        Returns userunits given a string representation of units in another system
    
    If unit is a string containing the unit to get the value in:
        Returns the value of the string in the units given in unit by looking for the conversion
        value in the UNITS[unit_type] dict.
    """
    if type(unit) is dict:
        return unittouu(string,unit)
    elif type(unit) is str:
        uu = unittouu(string,preferences.UNITS[unit_type])
        #print "unit_type %s, unit %s"%(unit_type,unit)
        return uu/preferences.UNITS[unit_type][unit]
    

def get_unit_model():
    length_units_model = Gtk.ListStore(str)
    for k in uuconv.keys():
        length_units_model.append([k])
    return length_units_model

# ====================================================================================
def callback(allow_blocking=True):
        def decorator(fn):
            """
            Checks if the field should be updated.
            Catches errors and sends them to a UI message window or log file.
            """
            def wrapped(self,*args,**kwargs):
                
                msg = "Event: %s.%s %s"%(self.__class__.__name__,fn.__name__,(self._block_callbacks and allow_blocking and "blocked") or "")
                print msg
                logging.debug(msg)
                if self._block_callbacks and allow_blocking:
                    #print "Block Callback: %s\nAllowBlocking:%s"%(self._block_callbacks,allow_blocking)
                    return None
                else: # call by default, only block if false
                    fn(self,*args,**kwargs)
                    if hasattr(self,"set_apply_sensitivty"):
                        self.set_apply_sensitivty()
                """
                TODO: This needs to be moved somewhere to catch exceptions and send
                messages to the UI...
                    log.debug(traceback.format_exc())
                    msg = Gtk.MessageDialog(type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        message_format="Error")
                    msg.format_secondary_text("Fricking iditio")
                    msg.run()
                    msg.destroy()
                """
            return wrapped
        
        #Check if it was called with an argument or not..
        if callable(allow_blocking):
            return decorator(allow_blocking)
        return decorator


class InkcutUIState():
    state_key = ""
    _block_callbacks = False
    # ===================== Callback helpers =============================
    def block_all_handlers(self):
        """ Will block all callback signals using the @callback decorator"""
        self._block_callbacks = True
        
    def unblock_all_handlers(self):
        """Will unblock all callback signals using the @callback decorator"""
        self._block_callbacks = False
        
    #####################################################################################
    #                                   UI STATE                                        #
    #####################################################################################

    def load_state(self,defaults,load_all=False):
        self.state = {
            "default":{self.state_key:defaults},
            "current":{self.state_key:{}},# current state, updated immediately
            "saved":{self.state_key:{}}, # previously saved state
            "global":{}, # All preferences, DO NOT UPDATE FROM THIS!
        }

        # Load the previous config from the preferences
        prefs = preferences.load()
        if load_all:
            self.state['global'] = prefs
        
        try:
            logging.info("Loaded %s settings from preferences..."%self.state_key)
            self.state['current'][self.state_key].update(prefs[self.state_key])

            # Do not make any changes to this except for when applying!!
            self.state['saved'][self.state_key].update(prefs[self.state_key])

            if not self.check_data_integity(): raise KeyError
        except KeyError,e:
            logging.info("Loaded default %s settings...\n(%s)"%(self.state_key,e))
            self.state['current'][self.state_key].update(self.state['default'][self.state_key])
            self.state['saved'][self.state_key].update(self.state['default'][self.state_key])

    def save_state(self,state_key=None):
        prefs = preferences.load()
        if state_key is not None:
            prefs[state_key].update(self.state['global'][state_key])
        else:
            self.state['saved'][self.state_key].update(self.state['current'][self.state_key])
            # TODO check file is OK here
            prefs[self.state_key].update(self.state['saved'][self.state_key])
            
        preferences.save(prefs)
    
    def check_data_integity(self):
        """Make sure our saved data state is in line with what we need"""
        try:
            for key in self.state['default'][self.state_key].keys():
                self.state['current'][self.state_key][key]
            return True
        except KeyError:
            return False

# ====================================================================================

class InkcutDialog(InkcutUIState):
    # ===================== Callback helpers =============================
    def set_apply_sensitivty(self):
        """ Determines if any changes have been made, if yes allow applying."""
        #pprint(self.state)
        if self.state['saved'][self.state_key] == self.state['current'][self.state_key]:
            self.ui['btn_apply'].set_sensitive(False)
        else:
            self.ui['btn_apply'].set_sensitive(True)
    
    # ===================== Dialog Button Callbacks =============================        
    @callback(False)
    def on_btn_apply_clicked(self,widget,data=None):
        """The user has elected to save the changes and continue editing."""
        self.save_state()
        self.set_apply_sensitivty()
        
    @callback(False)
    def on_btn_ok_clicked(self, widget, data=None):
        """The user has elected to save the changes and is finished editing."""
        self.on_btn_apply_clicked(widget,data)
        self.destroy()
        
    @callback(False)
    def on_btn_cancel_clicked(self, widget, data=None):
        """The user has elected cancel all unapplied changes."""
        self.destroy()
    
    @callback(False)
    def on_destroy(self, widget, data=None):
        """ Disregard any unapplied changes and close the dialog."""
        if self.toplevel:
            Gtk.main_quit()
        else:
            self.destroy()
    
