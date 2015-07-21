# -*- coding: utf-8 -*-
'''
Created on Jul 14, 2015

@author: jrm
'''
import os
import sys
import logging
from logging import Logger
from atom.api import Atom,Instance
from enaml.image import Image
from enaml.icon import Icon,IconImage
from enaml.workbench.plugin import Plugin as EnamlPlugin
from enaml.workbench.ui.ui_workbench import UIWorkbench
from IPython.config.loader import Config

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
    
    def _default_config(self):
        if self.workbench:
            return self.workbench.config
        return Config()
    
    def _observe_workbench(self,change):
        """ Watch for workbench config changes """
        self.workbench.observe('config',self._observe_config)
    
    def _observe_config(self,change):
        """ Update this classes items when the config changes """
        key = self.__class__.__name__
        if key not in self.config:
            self.config[key] = Config() 
        
        # Set instance attributes
        for k,v in self.config[key].items():
            if k in self.members() and v is not None:
                setattr(self,k,v)
        
        # Add to the config instancees
        if '__config_instances__' not in self.config[key]:
            self.config[key]['__config_instances__'] = []
        if self not in self.config[key]['__config_instances__']:
            self.config[key]['__config_instances__'].append(self)

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

class SingletonPlugin(Plugin,SingletonAtom):
    """ A plugin that only allows one instance."""