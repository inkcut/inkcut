"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 11, 2017

@author: jrm
"""
from atom.api import Unicode, Callable, Enum
from enaml.core.declarative import Declarative, d_

DOCK_ITEM_POINT = 'inkcut.ui.dock.items'


class DockItem(Declarative):

    #: The plugin to pass to this dock item
    plugin_id = d_(Unicode())

    #: The factory for creating this dock item
    factory = d_(Callable())

    #: Where to layout this item in the dock area
    layout = d_(Enum('main', 'top', 'left', 'right', 'bottom'))