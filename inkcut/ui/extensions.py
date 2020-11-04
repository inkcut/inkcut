"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 11, 2017

@author: jrm
"""
from atom.api import Str, Callable, Enum
from enaml.core.declarative import Declarative, d_

DOCK_ITEM_POINT = 'inkcut.ui.dock.items'
SETTINGS_PAGE_POINT = 'inkcut.ui.settings.page'


class DockItem(Declarative):

    #: The plugin to pass to this dock item
    plugin_id = d_(Str())

    #: The factory for creating this dock item
    factory = d_(Callable())

    #: Where to layout this item in the dock area
    layout = d_(Enum('main', 'top', 'left', 'right', 'bottom'))


class SettingsPage(Declarative):

    #: Settings page name that is displayed in the ui
    name = d_(Str())

    #: The plugin to pass to this dock item
    plugin_id = d_(Str())

    #: Attribute to pull from the plugin using getattr to retrieve the model
    #: for the settings page. If blank, the plugin will be used.
    model = d_(Str())

    #: The factory for creating this settings page. Must return a view class
    #: with a 'model' attribute to pass to a MappedView instance.
    factory = d_(Callable())
