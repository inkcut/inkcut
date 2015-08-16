# -*- coding: utf-8 -*-
'''
Created on Jul 14, 2015

@author: jrm
'''
import os
import sys
import logging
from logging import Logger
from atom.api import Atom,Instance,Bool
from enaml.image import Image
from enaml.icon import Icon,IconImage
from enaml.workbench.plugin import Plugin as EnamlPlugin
from enaml.workbench.ui.ui_workbench import UIWorkbench
from IPython.config.loader import Config
import json
from json.encoder import JSONEncoder

def icon_path(name):
    if hasattr(sys, 'frozen'):
        path =os.getcwd() # TODO: Do this
    else:
        path = os.getcwd()
    return os.path.join(path,'res','icons','%s.png'%name)

def load_image(name):
    with open(icon_path(name),'rb') as f:
        data = f.read()
    return Image(data=data)

def load_icon(name):
    img = load_image(name)
    icg = IconImage(image=img) 
    return Icon(images=[icg])

class SafeJsonEncoder(JSONEncoder):
    def default(self, o):
        return o
        

def config_to_json(config,fp):
    return json.dump(config,fp,cls=SafeJsonEncoder,indent=3,sort_keys=True)


class WorkbenchAtom(Atom):
    workbench = Instance(UIWorkbench)
    
    def _default_workbench(self):
        from inkcut.workbench.core.app import InkcutWorkbench
        return InkcutWorkbench.instance()

class LoggingAtom(WorkbenchAtom):
    log = Instance(Logger)
    
    def _default_log(self):
        if self.workbench:
            return self.workbench.log
        return logging.getLogger(self.__class__.__name__)
    
class ConfigurableAtom(LoggingAtom):
    config = Instance(Config)
    _config_lock = Bool()    
    def __init__(self,*args,**kwargs):
        super(ConfigurableAtom, self).__init__(*args,**kwargs)
        self.config # Load it
        self._init_config()
    
    def _default_config(self):
        if not self.workbench:
            raise RuntimeWarning("Cannot load config without a workbench!")
        return self.workbench.config
    
    @property
    def configurables(self):
        configurables = []
        for member in self.members().values():
            if member.metadata and 'config' in member.metadata:
                configurables.append(member)
        return configurables
    
    def _init_config(self):
        self.workbench.observe('config',self._observe_config)
        for member in self.configurables:
            self.observe(member.name,self._save_config)
            
    def _uninit_config(self):
        self.workbench.unobserve('config',self._observe_config)
        for member in self.configurables:
            self.unobserve(member.name,self._save_config)
    
    def _observe_config(self,change):
        """ Update this classes items when the config changes """
        print(change)
        if not self.config:
            return
        try:
            self._config_lock = True
            key = self.__class__.__name__
            if key not in self.config:
                self.config[key] = Config() 
            
            # Set instance attributes
            for k,v in self.config[key].items():
                if k in self.members() and v is not None:
                    setattr(self,k,v)
        finally:
            self._config_lock = False
                
    def _save_config(self,change):
        if self._config_lock or change['type']=='create':
            return
        print(change)
        if self.config is None:
            self.config = Config()
        
        config = self.config.copy()
        
        key = self.__class__.__name__
        if key not in self.config:
            config[key] = Config()
            
        for member in self.members().values():
            if member.metadata and 'config' in member.metadata:
                v = getattr(self,member.name)
                config[key][member.name] = v
                
        new_config = config
        if self.workbench.config:
            new_config = self.workbench.config.copy()
            new_config.merge(config)
        
        self.workbench.config = None
        self.workbench.config = new_config 

class SingletonAtom(ConfigurableAtom):
    _instance = None

    @classmethod
    def instance(cls):
        """ Get the global instance.

        Returns
        -------
        result : Instance or None
            The global instance, or None if one has not yet
            been created.

        """
        return cls._instance

    def __new__(cls, *args, **kwargs):
        """ Create a new instance.

        There may be only one instance in existence at any
        point in time. Attempting to create a new instance when one
        exists will raise an exception.

        """
        if cls._instance is not None:
            raise RuntimeError('An instance of %s already exists'%(cls.__name__))
        self = super(SingletonAtom, cls).__new__(cls, *args, **kwargs)
        cls._instance = self
        return self
    

class Plugin(EnamlPlugin,ConfigurableAtom):
    """ Always include a logger in the plugin """
    
    @property
    def workbench(self):
        """ Get the workbench which is handling the plugin.

        """
        if self.manifest:
            return self.manifest.workbench
        return self._default_workbench()

class SingletonPlugin(Plugin,SingletonAtom):
    """ A plugin that only allows one instance."""