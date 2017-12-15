"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import enaml
import pkg_resources
from atom.api import List, Unicode, Instance
from inkcut.core.api import Plugin, DockItem, log
from enaml.layout.api import AreaLayout, DockBarLayout, HSplitLayout
from . import extensions


class InkcutPlugin(Plugin):
    #: Project site
    wiki_page = Unicode("https;//www.codelv.com/projects/inkcut")

    #: Dock items to add
    dock_items = List(DockItem)
    dock_layout = Instance(AreaLayout)

    def start(self):
        """ Load all plugins, refresh the dock area and then 
        restore state from the disk (if any).
        
        """
        self.load_plugins()
        self._refresh_dock_items()

        super(InkcutPlugin, self).start()

    def load_plugins(self):
        """ Load all the plugins Inkcut is dependent on """
        w = self.workbench
        plugins = []
        with enaml.imports():
            #: TODO autodiscover these
            from inkcut.preview.manifest import PreviewManifest
            from inkcut.job.manifest import JobManifest
            from inkcut.device.manifest import DeviceManifest
            from inkcut.joystick.manifest import JoystickManifest
            from inkcut.console.manifest import ConsoleManifest
            plugins.append(PreviewManifest)
            plugins.append(JobManifest)
            plugins.append(DeviceManifest)
            plugins.append(JoystickManifest)
            plugins.append(ConsoleManifest)

            #: Load any plugins defined as extension points
            for entry_point in pkg_resources.iter_entry_points(
                    group='inkcut.plugin', name=None):
                plugins.append(entry_point.load())

        #: Install all of them
        for Manifest in plugins:
            w.register(Manifest())

    def _bind_observers(self):
        """ Setup the observers for the plugin.
        """
        super(InkcutPlugin, self)._bind_observers()
        workbench = self.workbench
        point = workbench.get_extension_point(extensions.DOCK_ITEM_POINT)
        point.observe('extensions', self._refresh_dock_items)

    def _unbind_observers(self):
        """ Remove the observers for the plugin.
        """
        super(InkcutPlugin, self)._unbind_observers()
        workbench = self.workbench
        point = workbench.get_extension_point(extensions.DOCK_ITEM_POINT)
        point.unobserve('extensions', self._refresh_dock_items)

    def create_new_area(self):
        """ Create the dock area 
        """
        with enaml.imports():
            from .dock import DockView
        area = DockView(
            workbench=self.workbench,
            plugin=self
        )
        return area

    def _refresh_dock_items(self, change=None):
        """ Reload all DockItems registered by any Plugins 
        
        Any plugin can add to this list by providing a DockItem 
        extension in their PluginManifest.
        
        """
        workbench = self.workbench
        point = workbench.get_extension_point(extensions.DOCK_ITEM_POINT)

        #: Layout spec
        layout = {
            'main': [],
            'left': [],
            'right': [],
            'bottom': [],
            'top': []
        }

        dock_items = []
        for extension in sorted(point.extensions, key=lambda ext: ext.rank):
            for declaration in extension.get_children(extensions.DockItem):
                #: Create the item
                DockItem = declaration.factory()
                item = DockItem(
                    plugin=workbench.get_plugin(declaration.plugin_id),
                    closable=False
                )

                #: Add to our layout
                layout[declaration.layout].append(item.name)

                #: Save it
                dock_items.append(item)

        #: Update items
        log.debug("Updating dock items: {}".format(dock_items))
        self.dock_items = dock_items
        self._refresh_layout(layout)

    def _refresh_layout(self, layout):
        """ Create the layout for all the plugins
        

        """
        items = layout.pop('main')
        main = HSplitLayout(*items) if len(items) > 1 else items[0]

        dockbars = [DockBarLayout(*items, position=side)
                    for side, items in layout.items() if items]

        #: Update layout
        self.dock_layout = AreaLayout(
            main,
            dock_bars=dockbars
        )