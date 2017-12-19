"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
from __future__ import print_function

import jsonpickle as pickle

from atom.api import Unicode

from enaml.widgets.api import Container
from enaml.workbench.ui.api import Workspace

import enaml
with enaml.imports():
    from inkcut.ui.manifest import UIManifest


class InkcutWorkspace(Workspace):
    """ A custom Workspace class for the crash course example.

    """
    #: Storage for the plugin manifest's id.
    _manifest_id = Unicode()

    def start(self):
        """ Start the workspace instance.

        This method will create the container content and register the
        provided plugin with the workbench.

        """
        self.content = Container(padding=0)
        manifest = UIManifest()
        self._manifest_id = manifest.id
        self.workbench.register(manifest)
        self.workbench.get_plugin('inkcut.ui')
        self.load_area()

    def stop(self):
        """ Stop the workspace instance.

        This method will unregister the workspace's plugin that was
        registered on start.

        """
        self.save_area()
        self.workbench.unregister(self._manifest_id)

    def save_area(self):
        """ Save the dock area for the workspace.

        """
        print("Saving dock area")
        area = self.content.find('dock_area')
        try:
            with open('inkcut.workspace.db', 'w') as f:
                f.write(pickle.dumps(area))
        except Exception as e:
            print("Error saving dock area: {}".format(e))
            return e

    def load_area(self):
        """ Load the dock area into the workspace content.

        """
        plugin = self.workbench.get_plugin("inkcut.ui")
        # try:
        #     #with open('inkcut.workspace.db', 'r') as f:
        #     #    area = pickle.loads(f.read())
        #     pass #: TODO:
        # except Exception as e:
        #     print(e)
        area = plugin.create_new_area()
        area.set_parent(self.content)
