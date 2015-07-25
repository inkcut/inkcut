#------------------------------------------------------------------------------
# Copyright (c) 2013, Nucleic Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#------------------------------------------------------------------------------
from atom.api import  Unicode, Callable

from enaml.widgets.api import StatusItem
from enaml.workbench.ui.api import Workspace


class InkcutWorkspace(Workspace):
    """ A custom Workspace class for the crash course example.

    This workspace class will instantiate the content and register an
    additional plugin with the workbench when it is started. The extra
    plugin can be used to add addtional functionality to the workbench
    window while this workspace is active. The plugin is unregistered
    when the workspace is stopped.

    """
    #: The enamldef'd Container to create when the workbench is started.
    content_factory = Callable()

    #: The enamldef'd PluginManifest to register on start.
    manifest_factory = Callable()

    #: Storage for the plugin manifest's id.
    _manifest_id = Unicode()
    
    @property
    def status_items(self):
        items = []
        for child in self.content.children:
            if isinstance(child, StatusItem):
                items.append(child)
        return items
    
    def start(self):
        """ Start the workspace instance.

        This method will create the container content and register the
        provided plugin with the workbench.

        """
        self.content = self.content_factory()
        manifest = self.manifest_factory()
        self._manifest_id = manifest.id
        self.workbench.register(manifest)
        self.workbench.get_plugin(manifest.id)

    def stop(self):
        """ Stop the workspace instance.

        This method will unregister the workspace's plugin that was
        registered on start.

        """
        self.workbench.unregister(self._manifest_id)
