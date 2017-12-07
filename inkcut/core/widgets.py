"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 7, 2017

@author: jrm
"""
from enaml.widgets.api import DockArea, DockItem


# -----------------------------------------------------------------------------
# Custom widgets
# -----------------------------------------------------------------------------
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
