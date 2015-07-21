# -*- coding: utf-8 -*-
'''
Created on Jul 12, 2015

@author: jrm
'''
import os
import json
import logging
import traceback
from atom.api import Unicode,Atom
from enaml.workbench.ui.api import UIWorkbench
from enaml.qt import QtGui
from inkcut.workbench.core.utils import SingletonAtom
from IPython.config.loader import JSONFileConfigLoader,Config
from inkcut.workbench.core.registry import collect_plugins



class InkcutWorkbench(UIWorkbench,SingletonAtom):
    
    status = Unicode()
    app_icon = Unicode('')
    config_file = Unicode('inkcut_config.json')
    log_dir = Unicode('~/.config/inkcut/workspace/profile_default/logs')
    working_dir = Unicode('~/.config/inkcut/workspace/profile_default')
    config_dir = Unicode('~/.config/inkcut/workspace/profile_default')
    
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
            return loader.load_config()
        except:
            self.log.error(traceback.format_exc())
            return Config()
        
    def _observe_config(self, change):
        super(InkcutWorkbench, self)._observe_config(change)
        if 'oldvalue' in change and len(self.config):
            self.save_config()
            
    def save_config(self):
        """ Save the instances config variables that are tagged as config """
        config = {}
        for k in self.config.keys():
            for inst in self.config[k]['__config_instances__']:
                if not isinstance(inst, Atom):
                    continue
                for member in inst.members():
                    if 'config' in member.metadata and member.metadata['config']:
                        config[k][member.name] = getattr(inst,member.name)
        
        config_path = os.path.join(self.config_dir,self.config_file)
        self.log.debug("Saving config to %s..."%config_path)
        with open(config_path,'w') as f:
            json.dump(config, f, indent=3, sort_keys=True)
        
    @property
    def window(self):
        try:
            ui = self.get_plugin('enaml.workbench.ui')
            return ui.window.proxy.widget
        except:
            return QtGui.QDialog()
    
    def show_critical(self,title,message,*args):
        return QtGui.QMessageBox.critical(self.window,title,message,*args)
        
    def show_warning(self,title,message,*args):
        return QtGui.QMessageBox.warning(self.window,title,message,*args)
        
    def show_information(self,title,message,*args):
        return QtGui.QMessageBox.information(self.window,title,message,*args)
    
    def show_about(self,title,message,*args):
        return QtGui.QMessageBox.about(self.window,title,message,*args)
    
    def register_plugins(self,path):
        """ Register all plugins found in the given path 
        @param package: Prefix of package where plugins exist in
                        dotted notation. Ex 'inkcut.plugins'
        """
        self.log.debug("Loading plugins from %s"%(path,))
        for plugin_def in collect_plugins(path,prefix='',log=self.log):
            try:
                self.register(plugin_def())
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
