# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 10, 2015

@author: jrm
"""
import logging
from inkcut.core.api import Plugin, log


class ConsolePlugin(Plugin):
    def is_supported(self):
        try:
            from enaml.qt import qt_ipython_console
            return True
        except ImportError as e:
            log.warning("IPython console plugin is missing dependencies")
            log.exception(e)
            return False

    def start(self):
        """ Set the log level for IPython stuff to warn """
        for name in ['ipykernel.inprocess.ipkernel', 'traitlets']:
            log = logging.getLogger(name)
            log.setLevel(logging.WARNING)
