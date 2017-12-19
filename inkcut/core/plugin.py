"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import os
import sys
import enaml
import logging
import traceback
from atom.api import Unicode
from inkcut.core.api import Plugin, log
from logging.handlers import RotatingFileHandler


class CorePlugin(Plugin):

    _log_filename = Unicode()
    _log_format = Unicode('%(asctime)-15s | %(levelname)-7s | %(name)s | %(message)s')

    def start(self):
        self.init_logging()
        log.debug("Inkcut started.")

        #: Load the cli plugin
        w = self.workbench
        with enaml.imports():
            from inkcut.cli.manifest import CliManifest
        w.register(CliManifest())

        #: Start it
        w.get_plugin('inkcut.cli')

        #: Start the default workspace
        w.application.deferred_call(self.start_default_workspace)

    def start_default_workspace(self):
        try:
            ui = self.workbench.get_plugin('enaml.workbench.ui')
            ui.select_workspace('inkcut.workspace')
        except SystemExit:
            raise
        except:
            log.error(traceback.format_exc())
            tb = traceback.format_exc().split("\n")
            msg = "\n".join(tb[max(-len(tb), -11):])
            self.workbench.message_critical("Workspace startup error",
                "An error prevented startup. This is either a bug or a "
                "required library is missing on your system. "
                "\n\n{}\n\n"
                "Please report this issue or request help at "
                "https://github.com/codelv/inkcut ".format(msg.strip()))
            raise

    def _default__log_filename(self):
        log_dir = os.path.expanduser('~/.config/inkcut/logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        return os.path.join(log_dir, 'inkcut.txt')

    def init_logging(self):
        """ Log to stdout and the file """
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        formatter = logging.Formatter(self._log_format)

        #: Log to stdout
        stream = logging.StreamHandler(sys.stdout)
        stream.setLevel(logging.DEBUG)
        stream.setFormatter(formatter)

        #: Log to rotating handler
        disk = RotatingFileHandler(
            self._log_filename,
            maxBytes=1024*1024*10,  # 10 MB
            backupCount=10,
        )
        disk.setLevel(logging.DEBUG)
        disk.setFormatter(formatter)

        root.addHandler(disk)
        root.addHandler(stream)

        #: Start twisted logger
        from twisted.python.log import PythonLoggingObserver
        observer = PythonLoggingObserver()
        observer.start()