# -*- coding: utf-8 -*-
'''
Created on Jul 12, 2015

@author: jrm
'''
import os
import logging
import traceback
from atom.api import Unicode,Int
from inkcut.workbench.ui.widgets.api import *
from enaml.workbench.ui.api import UIWorkbench
from enaml.qt import QtGui
from enaml.application import timed_call
from inkcut.workbench.core.utils import SingletonAtom, config_to_json
from inkcut.workbench.core.registry import collect_plugins
from IPython.config.loader import JSONFileConfigLoader,Config




class InkcutWorkbench(UIWorkbench,SingletonAtom):
    
    status = Unicode()
    app_name = Unicode('Inkcut')
    app_icon = Unicode('')
    config_file = Unicode('inkcut_config.json')
    log_dir = Unicode(os.path.expanduser('~/.config/inkcut/workspace/profile_default/logs'))
    working_dir = Unicode(os.path.expanduser('~/.config/inkcut/workspace/profile_default'))
    config_dir = Unicode(os.path.expanduser('~/.config/inkcut/workspace/profile_default'))
    _save_lock = Int()
    
    def _default_log(self):
        log = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)
        return log
    
    def _default_config(self):
        try:
            loader = JSONFileConfigLoader(filename=self.config_file,path=self.config_dir)
            config =  loader.load_config()
            self.log.debug("Loaded config %s"%config)
            return config
        except:
            self.log.error(traceback.format_exc())
            return Config()
        
    def _observe_config(self, change):
        """ This gets called a lot, so to minimize actual writes to the config file
        only write after a timer expires. """
        if not self.config:
            return
        super(InkcutWorkbench, self)._observe_config(change)
        if 'oldvalue' in change and change['oldvalue']!=change['value']:
            # Schedule a save to occur, if one is waiting, cancel it
            def save_job():
                """ If this is the last one scheduled, actually save 
                otherwise wait for the latest config (as more changes have occurred).
                """
                if self._save_lock==1:
                    self._save_config()
                self._save_lock-=1
            self._save_lock+=1
            timed_call(500,save_job)
            
    def _save_config(self):
        """ Save the instances config variables that are tagged as config """
        config_path = os.path.join(self.config_dir,self.config_file)
        self.log.debug("Saving config to %s..."%config_path)
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        with open(config_path,'w') as f:
            config_to_json(self.config,f)
        
    @property
    def window(self):
        """ Return the main UI window or a dialog if it wasn't made yet (during loading) """
        try:
            ui = self.get_plugin('enaml.workbench.ui')
            return ui.window.proxy.widget
        except:
            return QtGui.QDialog()
    
    def show_critical(self,title,message,*args):
        """ Popup a error dialog box """
        return QtGui.QMessageBox.critical(self.window,"{0} - {1}".format(self.app_name,title),message,*args)
        
    def show_warning(self,title,message,*args):
        return QtGui.QMessageBox.warning(self.window,"{0} - {1}".format(self.app_name,title),message,*args)
        
    def show_information(self,title,message,*args):
        return QtGui.QMessageBox.information(self.window,"{0} - {1}".format(self.app_name,title),message,*args)
    
    def show_about(self,title,message,*args):
        return QtGui.QMessageBox.about(self.window,"{0} - {1}".format(self.app_name,title),message,*args)
    
    def register_plugins(self,path):
        """ Register all plugins found in the given path 
        @param package: Prefix of package where plugins exist in
                        dotted notation. Ex 'inkcut.plugins'
        """
        self.log.debug("Loading plugins from %s"%(path,))
        for plugin_def in collect_plugins(path,prefix='',log=self.log):
            try:
                self.register(plugin_def())
            except ValueError:
                pass
            except:
                self.log.error(traceback.format_exc())
    
    def run(self):
        """ Run the UI workbench application.

        This method will load the core and ui plugins and start the
        main application event loop. This is a blocking call which
        will return when the application event loop exits.

        """
        import enaml
        with enaml.imports():
            from enaml.workbench.core.core_manifest import CoreManifest
            from enaml.workbench.ui.ui_manifest import UIManifest
            from inkcut.workbench.core.manifest import InkcutManifest

        self.register(CoreManifest())
        self.register(UIManifest())
        self.register(InkcutManifest())
        

        ui = self.get_plugin('enaml.workbench.ui')
        ui.select_workspace('inkcut.workbench.core.main_view')
        ui.show_window()
        ui.start_application()

        # TODO stop all plugins on app exit?
        #self.unregister('enaml.workbench.ui')
