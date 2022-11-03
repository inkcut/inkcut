"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 6, 2017

@author: jrm
"""
import os
import json
import enaml
import traceback
import jsonpickle as pickle
from atom.api import (
    Atom, Str, List, Member, Dict, Instance, ContainerList, Float, observe
)
from enaml.workbench.plugin import Plugin as EnamlPlugin
from enaml.widgets.api import Container
from enaml.qt import QtCore, QtGui
from .utils import log, clip


# -----------------------------------------------------------------------------
# Core models
# -----------------------------------------------------------------------------
class Model(Atom):
    """ An atom object that can exclude members from it's state
    by tagging the member with .tag(persist=False)

    """

    def __getstate__(self):
        """ Exclude any members from the state that are not tagged with
        `config=True`.

        """
        state = super(Model, self).__getstate__()
        for name, member in self.members().items():
            metadata = member.metadata
            if (name in state and (not metadata or
                    not metadata.get('config', False))):
                del state[name]
        return state

    def __setstate__(self, state):
        """  Set the state ignoring any fields that fail to set which
        may occur due to version changes.

        """
        for key, value in state.items():
            log.debug("Restoring state '{}.{} = {}'".format(
                self, key, clip(value)
            ))
            try:
                setattr(self, key, value)
            except Exception as e:
                #: Shorten any long values
                log.warning("Failed to restore state '{}.{} = {}'".format(
                    self, key, clip(value)
                ))


class AreaBase(Model):
    #: Size (in px)
    size = ContainerList(Float(), default=[1800, 2700]).tag(config=True)

    # Left, Top, Right, Bottom (in px)
    padding = ContainerList(Float(),
                            default=[10, 10, 10, 10]).tag(config=True)

    area = Instance(QtCore.QRectF)
    path = Instance(QtGui.QPainterPath)
    padding_path = Instance(QtGui.QPainterPath)

    def _default_area(self):
        return QtCore.QRectF(0, 0, self.size[0], self.size[1])

    def _default_path(self):
        p = QtGui.QPainterPath()
        p.addRect(self.area)
        return p

    def _default_padding_path(self):
        p = QtGui.QPainterPath()
        p.addRect(self.available_area)
        return p

    @observe('size', 'padding')
    def _sync_size(self, change):
        self.area.setWidth(self.size[0])
        self.area.setHeight(self.size[1])
        self.path = self._default_path()
        self.padding_path = self._default_padding_path()

    @property
    def padding_left(self):
        return self.padding[0]

    @property
    def padding_top(self):
        return self.padding[1]

    @property
    def padding_right(self):
        return self.padding[2]

    @property
    def padding_bottom(self):
        return self.padding[3]

    def width(self):
        return self.size[0]

    def height(self):
        return self.size[1]

    @property
    def available_area(self):
        x, y = self.padding_left, self.padding_bottom
        w, h = (self.size[0]-(self.padding_right+self.padding_left),
                self.size[1]-(self.padding_bottom+self.padding_top))
        return QtCore.QRectF(x, y, w, h)


class Plugin(EnamlPlugin):
    """ A plugin that behaves like a model and saves it's state
    when any atom member tagged with config=True triggers a save.

    Also optionally registers itself in the settings

    """

    #: Settings pages this plugin adds
    settings_pages = Dict(Atom, Container)
    settings_items = List(Atom)

    #: File used to save and restore the state for this plugin
    _state_file = Str()
    _state_excluded = List()
    _state_members = List(Member)

    # -------------------------------------------------------------------------
    # Plugin API
    # -------------------------------------------------------------------------
    def is_supported(self):
        """ If this plugin is optional, return whether the plugin can be
        used.  Plugins that are not required can be ignored.
        """
        return True

    def start(self):
        """ Load the state when the plugin starts """
        log.debug("Starting plugin '{}'".format(self.manifest.id))
        self._bind_observers()

    def stop(self):
        """ Unload any state observers when the plugin stops"""
        self._unbind_observers()

    def run_command(self, protocol,  *args, **kwargs):
        """ Run a command without blocking using twisted's spawnProcess

        See https://twistedmatrix.com/documents/current/core/howto/process.html

        """
        # Importing reactor has sidefects which can interfer with testing.
        #  Don't import it at top level of common utilities like models.
        from twisted.internet import reactor
        log.info(" ".join(args))
        return reactor.spawnProcess(protocol, args[0], args, **kwargs)

    # -------------------------------------------------------------------------
    # State API
    # -------------------------------------------------------------------------
    def save(self):
        """ Manually trigger a save """
        self._save_state({'type': 'request'})

    def _default__state_file(self):
        return os.path.expanduser(
            "~/.config/inkcut/{}.json".format(self.manifest.id))

    def _default__state_members(self):
        members = []  #: Init state members
        for name, member in self.members().items():
            if member.metadata and member.metadata.get('config', False):
                members.append(member)
        return members

    def _bind_observers(self):
        """ Try to load the plugin state """
        #: Restore
        try:
            with enaml.imports():
                with open(self._state_file, 'r') as f:
                    state = pickle.loads(f.read())
            #with self.suppress_notifications():
            self.__setstate__(state)
            log.warning("Plugin {} state restored from: {}".format(
                self.manifest.id, self._state_file))
        except IOError as e:
            pass  #: No state
        except Exception as e:
            log.warning("Plugin {} failed to load state: {}".format(
                self.manifest.id, traceback.format_exc()))

        #: Hook up observers
        for member in self._state_members:
            self.observe(member.name, self._save_state)

    def _save_state(self, change):
        """ Try to save the plugin state """
        if change['type'] in ['update', 'container', 'request']:
            try:
                log.info("Saving state due to change: {}".format(change))

                #: Dump first so any failure to encode doesn't wipe out the
                #: previous state
                state = self.__getstate__()
                excluded = ['manifest', 'workbench'] + [
                    m.name for m in self.members().values()
                    if not m.metadata or not m.metadata.get('config', False)
                ]
                for k in excluded+self._state_excluded:
                    if k in state:
                        del state[k]
                state = pickle.dumps(state)

                #: Pretty format it
                state = json.dumps(json.loads(state), indent=2)

                dst = os.path.dirname(self._state_file)
                if not os.path.exists(dst):
                    os.makedirs(dst)

                with open(self._state_file, 'w') as f:
                    f.write(state)

            except Exception as e:
                log.warning("Failed to save state: {}".format(
                    traceback.format_exc()
                ))

    def _unbind_observers(self):
        """ Setup state observers """
        for member in self._state_members:
            self.unobserve(member.name, self._save_state)

    # -------------------------------------------------------------------------
    # Settings API
    # -------------------------------------------------------------------------
    def _default_settings_pages(self):
        """ Available settings pages """
        return {}

    def _default_settings_items(self):
        return []

