"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import sys
import logging
from atom.api import Unicode
from inkcut.core.api import Plugin


class CorePlugin(Plugin):

    _log_format = Unicode('%(asctime)-15s | %(levelname)s | %(message)s')

    def start(self):
        self.init_logging()
        self.workbench.application.deferred_call(self.start_default_workspace)

    def start_default_workspace(self):
        ui = self.workbench.get_plugin('enaml.workbench.ui')
        ui.select_workspace('inkcut.workspace')

    def init_logging(self):
        log = logging.getLogger('inkcut')
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(self._log_format))
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)

        from twisted.python import log
        log.startLogging(sys.stdout)