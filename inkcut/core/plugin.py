"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import sys

from inkcut.core.api import Plugin


class CorePlugin(Plugin):

    def start(self):
        self.init_logging()
        self.workbench.application.deferred_call(self.start_default_workspace)

    def start_default_workspace(self):
        ui = self.workbench.get_plugin('enaml.workbench.ui')
        ui.select_workspace('inkcut.workspace')

    def init_logging(self):
        from twisted.python import log
        log.startLogging(sys.stdout)