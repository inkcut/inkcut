# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012 Jairus Martin - Vinylmark LLC <jrm@vinylmark.com>
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
Provides a shared preferences dictionary that contains a complete state of the
applications settings.
"""
import json
import os
import logging
logger = logging.getLogger('inkcut')

CONFIG_FILE = os.path.join(os.getenv("HOME"),'.config','inkcut','data','preferences.json')
TEST_FILE = os.path.join(os.getenv("HOME"),'.config','inkcut','data','test.hpgl')

from device import DEFAULT_PROPERTIES as DEVICE_PROPERTIES
#from inkcut_lib.plot import DEFAULT_PROPERTIES as PLOT_PROPERTIES
from material import DEFAULT_PROPERTIES as MATERIAL_PROPERTIES

"""
App globals
"""
PREVIEWING_MODES = ['svg']#,'png','pdf']
DRAWING_MODES = ['svg']#,'hpgl','gpgl']
PLUGIN_EXTENSIONS = ['*.svg']#,'*.hpgl','*.gpgl','*.pdf','*.ai']
GRAPHIC_ROTATIONS = ['0 Degrees Clockwise','90 Degrees Clockwise','180 Degrees Clockwise','270 Degrees Clockwise']
PLOT_ORDERS = ['One Copy at a Time','Best Tracking','Shortest Path']


"""
Default Inkcut application preferences
"""
APP_PREFERENCES = {
    'app_version':2.0,
    'preferences_version':1.0, # TODO: when load() is called check that the preferences versions match!
    'drawing_mode':'svg', 
    'previewing_mode':'svg',
    'last_file_open_dir':None,
    'current_device':None,
    'current_material':None,
    'zoom':1.0,
}

PLOT_PROPERTIES = {
    'graphic_copies':1,
    'graphic_rotation':GRAPHIC_ROTATIONS[0],
    'graphic_scale_x':1,
    'graphic_scale_y':1,
    'graphic_scale_lock':True,
    'graphic_spacing_x':'10mm',
    'graphic_spacing_y':'10mm',
    'graphic_mirror_x':False,
    'graphic_mirror_y':False,
    'graphic_weedline':False,
    'graphic_auto_rotate':False,
    'plot_center_x':False,
    'plot_center_y':False,
    'plot_position_x':'0mm',
    'plot_position_y':'0mm',
    'plot_return_origin':False,
    'plot_feed_distance':'0mm',
    'plot_order':PLOT_ORDERS[0],
    'plot_weedline':False,
}


"""
The dictonary below contains lists of every unit and type used in the
Inkcut app.
"""
UNITS = {
    'force':{'g':1},
    'speed':{'cm/s':1,'mm/s':0.1,'in/s':2.54},
    'resolution':{'steps/in':0.011111111111111111},# =1/90
    'length':{'cm':35.433070866, 'ft':1080, 'in':90.0, 'km':3543307.0866,'pc':15.0,  
			'pt':1.25, 'px':1, 'm':3543.3070866,'mm':3.5433070866, 'yd':3240},
    'filesize':{'B':1,'KB':1000,'MB':10**6},
    'currency':{'$/in':1,'c/in':0.01}
}

"""
Push all default preferences into one dictionary
"""
DEFAULT_PREFERENCES = {
    'app':APP_PREFERENCES,
    'device':DEVICE_PROPERTIES,
    'plot':PLOT_PROPERTIES,
    'material':MATERIAL_PROPERTIES,
    'units':UNITS,
}

def load(config_file=CONFIG_FILE):
    """ Loads default preferences and updates the defaults with a config file. """
    preferences = DEFAULT_PREFERENCES
    try:
        f = open(config_file)
        config = json.load(f)
        for key in preferences.keys():
            try:
                preferences[key].update(config[key])
            except:
                logging.info("Attempt to load preferences[%s] failed. Using default value."%(key))
        f.close()
    except: 
        logging.info("Attempt to load preferences from %s failed. Using defaults."%(CONFIG_FILE))
    return preferences

def defaults():
    return DEFAULT_PREFERENCES

def save(preferences,config_file=CONFIG_FILE):
    """ Loads default preferences and updates the defaults with a config file. """
    config_dir = os.path.dirname(config_file)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    f = open(config_file,'w+')	
    json.dump(preferences,f,indent=2)
    f.close()    
    
