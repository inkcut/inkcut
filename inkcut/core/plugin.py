"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import enaml
import traceback
from inkcut.core.api import Plugin, log


class CorePlugin(Plugin):

    def start(self):
        self.init_logging()
        log.debug("Inkcut loaded.")

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

    def init_logging(self):
        """ Initialize twisted logging  """
        #: Start twisted logger
        from twisted.python.log import PythonLoggingObserver
        observer = PythonLoggingObserver()
        observer.start()
        
