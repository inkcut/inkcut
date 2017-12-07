"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import os
import sys
import traceback
import jsonpickle as pickle
from atom.api import Atom, Unicode, List, Member, Dict
from future.builtins import str
from enaml.image import Image
from enaml.icon import Icon, IconImage
from enaml.workbench.plugin import Plugin as EnamlPlugin
from enaml.widgets.api import Container, DockArea, DockItem
from enaml.application import timed_call
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from .svg import QtSvgDoc

#: Cache for icons
_IMAGE_CACHE = {}


def icon_path(name):
    """ Load an icon from the res/icons folder using the name 
    without the .png
    
    """
    path = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(path, 'res', 'icons', '%s.png' % name)


def load_image(name):
    """ Get and cache an enaml Image for the given icon name.
    
    """
    path = icon_path(name)
    global _IMAGE_CACHE
    if path not in _IMAGE_CACHE:
        with open(path, 'rb') as f:
            data = f.read()
        _IMAGE_CACHE[path] = Image(data=data)
    return _IMAGE_CACHE[path]


def load_icon(name):
    img = load_image(name)
    icg = IconImage(image=img)
    return Icon(images=[icg])


def menu_icon(name):
    """ Icons don't look good on Linux/osx menu's """
    if sys.platform == 'win32':
        return load_icon(name)
    return None


def from_unit(val, unit='px'):
    return QtSvgDoc.convertFromUnit(val, unit)


def to_unit(val, unit='px'):
    return QtSvgDoc.convertToUnit(val, unit)


def async_sleep(ms):
    """ Sleep for the given duration without blocking. Typically this
    is used with the inlineCallbacks decorator.
    """
    d = Deferred()
    timed_call(ms, d.callback, True)
    return d


class Model(Atom):
    """ An atom object that can exclude members from it's state
    by tagging the member with .tag(persist=False)
    
    """

    def __getstate__(self):
        """ Exclude any members from the state that are
        tagged with `persist=False`. 
        
        """
        state = super(Model, self).__getstate__()
        for name, member in self.members().items():
            metadata = member.metadata
            if name in state and metadata and \
                    not metadata.get('persist', True):
                del state[name]
        return state

    def __setstate__(self, state):
        """  Set the state ignoring any fields that fail to set which
        may occur due to version changes.
        
        """
        for key, value in state.items():
            try:
                setattr(self, key, value)
            except Exception as e:
                #: Shorten any long values
                v = str(value)
                if len(v) > 100:
                    v[:100]+"..."

                print("Failed to restore state '{}.{} = {}'".format(
                    self, key, v
                ))


class Plugin(EnamlPlugin):
    """ A plugin that behaves like a model and saves it's state
    when any atom member not tagged with persist=False triggers a save.
     
    Also optionally registers itself in the settings
    
    """

    #: Settings pages this plugin adds
    settings_pages = Dict(Atom, Container).tag(persist=False)
    settings_items = List(Atom)

    #: File used to save and restore the state for this plugin
    _state_file = Unicode().tag(persist=False)
    _state_excluded = List(str).tag(persist=False)
    _state_members = List(Member).tag(persist=False)

    # -------------------------------------------------------------------------
    # Plugin API
    # -------------------------------------------------------------------------
    def start(self):
        """ Load the state when the plugin starts """
        self._bind_observers()

    def stop(self):
        """ Unload any state observers when the plugin stops"""
        self._unbind_observers()

    def run_command(self, protocol,  *args, **kwargs):
        """ Run a command without blocking using twisted's spawnProcess 
        
        See https://twistedmatrix.com/documents/current/core/howto/process.html
        
        """
        print(" ".join(args))
        return reactor.spawnProcess(protocol, args[0], args, **kwargs)

    # -------------------------------------------------------------------------
    # State API
    # -------------------------------------------------------------------------
    def _default__state_file(self):
        return os.path.expanduser(
            "~/.config/inkcut/{}.json".format(self.manifest.id))

    def _default__state_members(self):
        members = []  #: Init state members
        for name, member in self.members().items():
            if not member.metadata or member.metadata.get('persist', True):
                members.append(member)
        return members

    def _bind_observers(self):
        """ Try to load the plugin state """
        #: Restore
        try:
            with open(self._state_file, 'r') as f:
                state = pickle.loads(f.read())
            self.__setstate__(state)
        except Exception as e:
            print("Failed to load state: {}".format(e))

        #: Hook up observers
        for member in self._state_members:
            self.observe(member.name, self._save_state)

    def _save_state(self, change):
        """ Try to save the plugin state """
        if change['type'] in ['update', 'container']:
            try:
                print("Saving state due to change: {}".format(change))

                #: Dump first so any failure to encode doesn't wipe out the
                #: previous state
                state = self.__getstate__()
                excluded = ['manifest', 'workbench'] + [
                    m.name for m in self.members().values()
                    if m.metadata and not m.metadata.get('persist', True)
                ]
                for k in excluded+self._state_excluded:
                    if k in state:
                        del state[k]
                state = pickle.dumps(state)

                dst = os.path.dirname(self._state_file)
                if not os.path.exists(dst):
                    os.makedirs(dst)

                with open(self._state_file, 'w') as f:
                    f.write(state)

            except Exception as e:
                print("Failed to save state:")
                traceback.print_exc()

    def _unbind_observers(self):
        """ Setup state observers """
        for member in self._state_members:
            if not member.metadata or member.metadata.get('persist', True):
                self.unobserve(member.name, self._save_state)

    # -------------------------------------------------------------------------
    # Settings API
    # -------------------------------------------------------------------------
    def _default_settings_pages(self):
        """ Available settings pages """
        return {}

    def _default_settings_items(self):
        return []


class PickableDockItem(DockItem):
    """ A custom pickable dock item class.

    """
    def __getstate__(self):
        """ Get the pickle state for the dock item.

        This method saves the necessary state for the dock items used
        in this example. Different applications will have different
        state saving requirements.

        The default __setstate__ method provided on the Atom base class
        provides sufficient unpickling behavior.

        """
        return {'name': self.name, 'title': self.title}


class PickableDockArea(DockArea):
    """ A custom pickable dock area class.

    """
    def get_save_items(self):
        """ Get the list of dock items to save with this dock area.

        """
        return [c for c in self.children if isinstance(c, PickableDockItem)]

    def __getstate__(self):
        """ Get the pickle state for the dock area.

        This method saves the necessary state for the dock area used
        in this example. Different applications will have different
        state saving requirements.

        """
        state = {
            'name': self.name,
            'layout': self.save_layout(),
            'items': self.get_save_items(),
        }
        return state

    def __setstate__(self, state):
        """ Restore the state of the dock area.

        """
        self.name = state['name']
        self.layout = state['layout']
        self.insert_children(None, state['items'])
