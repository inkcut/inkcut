# -*- coding: utf-8 -*-
'''
Created on Jul 19, 2015

@author: jrm
'''
import os
import enaml
import fnmatch
import inspect
import importlib
import traceback
from enaml.workbench.plugin_manifest import PluginManifest

def collect_data_files(path,inc=['*.*'],exc=['*.pyc','*.enamlc']):
    # traverse root directory, and list directories as dirs and files as files
    data_files = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if not filter(lambda it:fnmatch.fnmatch(f,it),inc):
                continue
            elif filter(lambda it:fnmatch.fnmatch(f,it),exc):
                continue
            else:
                data_files.append(os.path.join(root,f))
                     
    return data_files

def collect_plugins(path,prefix='inkcut',log=None):
    plugins = []
    for plugin_file in collect_data_files(path, inc=['*.enaml']):
        with enaml.imports():
            try:
                
                # Import the file
                plugin_path = os.path.splitext(plugin_file)[0].replace("\\","/").split("/")
                plugin_path = '.'.join([prefix]+plugin_path)
                mod = importlib.import_module(plugin_path)
                
                # Find any PluginManifest subclasses
                for name,obj in inspect.getmembers(mod):
                    if inspect.isclass(obj) and issubclass(obj,PluginManifest) and obj!=PluginManifest:
                        if log:
                            log.debug("Loaded %s"%(obj,))
                        plugins.append(obj)
            except:
                if log:
                    log.debug("PluginLoadError:%s",traceback.format_exc())
    return plugins