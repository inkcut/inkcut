'''
Created on Sep 2, 2016

@author: jrm
'''
import os
import json
import traceback
import copy_reg
import jsonpickle as pickle

from atom.api import Bool,Int, Dict, Unicode, Instance, List, Subclass
from enaml.application import timed_call
from enaml.core.api import Declarative,d_
from enaml.widgets.api import Container
from inkcut.workbench.core.utils import LoggingAtom,SingletonPlugin

PREFERENCES_POINT = 'inkcut.preferences.items'

class Preference(Declarative):
    #: Plugin store the preference as
    plugin_id = d_(Unicode())
    
    #: Attributes of this plugin to save and restore
    #: Restoring occurs during loading of the plugin
    attributes = d_(Instance((list,tuple)))
    
    #: View to display within the preferences page
    #: If none is given no page will be created
    #: the container must have a name and plugin attributes
    view_class = d_(Subclass(Container))
    

class Model(LoggingAtom):
    """ Base class of models that need to retain state. 
        Allows restoring state even if properties change 
        by warning instead of failing. 
        
        Will by default save when any property changes that
        is not tagged with autosave=False or persist=False.
        
        Also, you can exclude properties from saving by tagging with 
        persist=False.
        
    """
    __restoring__ = Bool(False).tag(persist=False)
    
    def __init__(self,*args,**kwargs):
        super(Model, self).__init__(*args,**kwargs)
        self._bind_save_observers()
        
    def _bind_save_observers(self):
        """ Bind all members that should cause a save to occur.
            This model will only be saved if it is in the `State.models`
            list or is in the state of a member that is.
        """
        for name,member in self.members().iteritems():
            if (member.metadata and 
                ((member.metadata.get('autosave',True) 
                  or member.metadata.get('config',False))
                 )):
                self.observe(name,self.save)
    
    def __getstate__(self):
        state = {}
        state.update(getattr(self, '__dict__', {}))
        slots = copy_reg._slotnames(type(self))
        if slots:
            for name in slots:
                state[name] = getattr(self, name)
                
        for key,member in self.members().iteritems():
            if member.metadata and member.metadata.get('config',False):
                state[key] = getattr(self, key)
        return state
    
    def __setstate__(self, state):
        self.log.debug("Setting state of {} to {}".format(self,state))
        try:
            self.__restoring__ = True
        
            for key, value in state.iteritems():
                if hasattr(self, key):
                    try:
                        setattr(self, key, value)
                    except Exception as e:
                        self.log.error("Could not restore {} on {} to {}: {}".format(key,self,value,e))
                else:
                    self.log.warning("Could not restore {} on {}, property missing or renamed.".format(key,self))
        finally:
            self.__restoring__ = False
        self._bind_save_observers()
        self.log.debug("Restored state of {} is {}".format(self,self.__getstate__()))
    
    def _is_restoring(self):
        """ Use this to check if the saved state is currently being restored.
            So you can avoid making changes while restoring state """
        return self.__restoring__
    
    
    def clone(self):
        obj = self.__class__()
        obj.__setstate__(self.__getstate__())
        return obj
    
    def save(self,change={}):
        PreferencePlugin.instance().save(change)
                
class PreferencePlugin(SingletonPlugin):
    """ Class for saving and restoring 
        application state. 
    """ 
    
    #: Used to check if state is being loaded
    _loading = True
    
    #: Count of pending saves so saving can
    #: be deferred and only done once when
    #: multiple changes occur quickly.
    _pending = Int(0)
    
    #: Time in ms to delay before saving
    delay = Int(200)
    
    #: List of models to be saved. Only 'Root' models
    #: should be included.
    load_state = Dict(basestring,dict)
    default_state = Dict(basestring,dict)
    
    #: Filename of state file
    resource = Unicode('.config/inkcut/state.json')
    
    _preferences = List(Preference)
#     @classmethod
#     def instance(cls):
#         if not cls._instance:
#             try:
#                 cls._loading = True
#                 with open('state.json','rb') as f:
#                     cls._instance = jsonpickle.loads(f.read())
#             except:
#                 cls._instance = cls()
#             finally:
#                 cls._loading = False
#         return cls._instance

    def start(self):
        self._bind_observers()
        self._on_preferences_updated()
        self.load()
        
    def stop(self):
        self._unbind_observers()
        
    def save(self,change={}):
        """ Method to use to save this to save the state.
            this queues up a save task that will be
            run after `delay` ms.
        """
        self._pending +=1
        timed_call(self.delay,self._schedule_save,change)
        
    def _schedule_save(self,change={}):
        """ Actually perform the save operation when all
            pending calls have completed.
        """
        self._pending -=1
        if self._pending==0:
            try:
                self.log.debug("Saving state due to change: {}".format(change))
                if not os.path.exists(os.path.dirname(self.resource)):
                    os.makedirs(os.path.dirname(self.resource))
                with open(self.resource,'wb') as f:
                    state = json.dumps(
                                    # Load with json so it can be saved in a more readable format
                                    json.loads(pickle.dumps(self.current_state)),
                                    indent=4)
                    self.log.debug("State saved is: {}".format(state))
                    f.write(state)
                self.log.debug("State saved to {}!".format(self.resource))
            except Exception as e:
                self.log.error("Error saving state: {}".format(traceback.format_exc()))
        
    def load(self):
        """ Attempt to read a previously saved state from the file path
            given by the `self.resource` attribute.
        """
        try:
            self.log.debug("Loading state from {}".format(self.resource))
            with open(self.resource,'rb') as f:
                self.load_state = pickle.loads(f.read())
            self.restore(self.load_state)
        except:
            self.log.error("Error loading state: {}".format(traceback.format_exc()))
            
    def restore(self,state):
        for plugin_id in state:
            self.sync_state(plugin_id)
            
    def sync_state(self,plugin_id):
        """ Sync plugin state with loaded state. """
        try:
            plugin = self.workbench.get_plugin(plugin_id)
            if plugin_id in self.load_state:
                # This only does single levels...?
                self.log.debug("Loading plugin '{}' state: {}".format(plugin_id,self.load_state[plugin_id]))
                plugin.__setstate__(self.load_state[plugin_id])
        except Exception as e:
            self.log.error("Error restoring state for '{}': {}".format(plugin_id,traceback.format_exc()))
                
    def _bind_observers(self):
        """ Setup the observers for the plugin.

        """
        workbench = self.workbench

        point = workbench.get_extension_point(PREFERENCES_POINT)
        point.observe('extensions', self._on_preferences_updated)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.

        """
        workbench = self.workbench
        
        point = workbench.get_extension_point(PREFERENCES_POINT)
        point.unobserve('extensions', self._on_preferences_updated)
        
    def _get_preferences(self):
        """ Get the preferences extension objects.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(PREFERENCES_POINT)
        extensions = sorted(point.extensions, key=lambda ext: ext.rank)
        
        preferences = []
        for extension in extensions:
            preferences.extend(extension.get_children(Preference))

        return preferences
    
    def _on_preferences_updated(self,change={}):
        """ When a plugin is loaded, attempt to restore the state """
        old = self._preferences
        preferences = self._get_preferences()
        for p in preferences:
            if p not in old:
                self.sync_state(p.plugin_id)
        self._preferences = preferences
    
    @property
    def current_state(self):
        state = {}
        for p in self._get_preferences():
            try:
                plugin = self.workbench.get_plugin(p.plugin_id)
                state[p.plugin_id] = {m:v for m,v in plugin.__getstate__().iteritems() if m in p.attributes}
            except:
                self.log.error("Failed to retrieve state from plugin {}".format(p.plugin_id))
        return state
        
    def _observe_state(self,change):
        self.log.debug("State changed {}".format(change))
        