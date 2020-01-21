"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import os
import enaml
import traceback
from atom.api import Enum
from inkcut.core.api import Plugin, log


ERROR_TEMPLATE = """
<html>
<h3>Sorry, an error prevented Inkcut from starting</h3>
<p>
This is either a bug or a required library may be missing on your system.
As always you can request help on the forums at
<a href="https://inkcut.org">https://inkcut.org</a>.
</p>

<p>
First try to restart the application. If the error persists you can try
clearing the saved settings in <a href="{config_dir}">{config_dir}</a>
and restart the application again</a>.
</p>

<p>
If that still doesn't work please report a new issue at
<a href="https://github.com/codelv/inkcut">https://github.com/codelv/inkcut</a>
with the following error:
</p>

<pre>{error}</pre>

<p> and include the logs from <a href="{log_dir}">{log_dir}</a>.
</p>
</html>
"""


ALL_TRANSLATIONS = (
    'English',
    'French',
    'German',
)


class CorePlugin(Plugin):
    #: Language
    #: These should match members of the QtCore.QLocale language
    language = Enum('system', *sorted(ALL_TRANSLATIONS)).tag(config=True)

    def start(self):
        self.init_logging()
        super(CorePlugin, self).start()
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
            config_dir = os.path.dirname(self._state_file)
            log_dir = os.path.join(config_dir, 'logs')
            self.workbench.message_critical(
                "Workspace startup error",
                ERROR_TEMPLATE.format(config_dir=config_dir,
                                      error=msg.strip(),
                                      log_dir=log_dir))
            raise

    def init_logging(self):
        """ Initialize twisted logging  """
        #: Start twisted logger
        from twisted.python.log import PythonLoggingObserver
        observer = PythonLoggingObserver()
        observer.start()
