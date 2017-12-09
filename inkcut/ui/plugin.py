"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import enaml
from atom.api import List, Unicode
from inkcut.core.api import Plugin, Model, DockItem, svg


class InkcutPlugin(Plugin):
    #: Project site
    wiki_page = Unicode("https;//www.codelv.com/projects/inkcut")

    #: Dock items to add
    dock_items = List(DockItem)

    def start(self):
        """ Load all the plugins Inkcut is dependent on """
        super(InkcutPlugin, self).start()
        w = self.workbench
        with enaml.imports():
            #: TODO autodiscover these
            from inkcut.job.manifest import JobManifest
            from inkcut.preview.manifest import PreviewManifest
            from inkcut.joystick.manifest import JoystickManifest
            w.register(JobManifest())
            w.register(PreviewManifest())
            w.register(JoystickManifest())

    def create_new_area(self):
        with enaml.imports():
            from .dock import DockView
        area = DockView(
            workbench=self.workbench,
            plugin=self
        )
        return area