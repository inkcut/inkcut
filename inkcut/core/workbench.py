"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import os
import signal

#: Must be installed before enaml is imported
import enamlx
enamlx.install()

import enaml
from atom.api import Str, Instance
from qtpy import API_NAME
from enaml.qt import QT_API, QtCore, QtWidgets, QtGui
from enaml.workbench.ui.api import UIWorkbench
from inkcut.core.utils import log



def pyside_dialog_patch():
    # Apply patch from https://github.com/nucleic/enaml/pull/111/files
    from atom.api import atomref
    from enaml.qt.qt_dialog import QWindowDialog
    from enaml.qt.q_window_base import QWindowLayout

    def __init__(self, proxy, parent, flags=QtCore.Qt.Widget):
        """ Initialize a QWindowDialog.

         Parameters
         ----------
         parent : QWidget, optional
             The parent of the dialog.
        """
        super(QWindowDialog, self).__init__(parent, flags)
        # PySide2 segfaults
        self._proxy_ref = None if QT_API in 'pyside2' else atomref(proxy)
        self._expl_min_size = QtCore.QSize()
        self._expl_max_size = QtCore.QSize()
        layout = QWindowLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)
        self.setLayout(layout)

    QWindowDialog.__init__ = __init__
    pyside_dialog_patch.applied = True
pyside_dialog_patch.applied = False


if 'pyside' in QT_API and not pyside_dialog_patch.applied:
    pyside_dialog_patch()

# Keep in sync
os.environ['PYQTGRAPH_QT_LIB'] = API_NAME


class InkcutWorkbench(UIWorkbench):
    #: Singleton instance
    _instance = None

    #: For error messages
    app_name = Str('Inkcut')

    #: Save reference to the translator
    translator = Instance(QtCore.QTranslator, ())

    @classmethod
    def instance(cls):
        return cls._instance

    @property
    def application(self):
        ui = self.get_plugin('enaml.workbench.ui')
        return ui._application

    @property
    def window(self):
        """ Return the main UI window or a dialog if it wasn't made yet
        (during loading)

        """
        try:
            ui = self.get_plugin('enaml.workbench.ui')
            return ui.window.proxy.widget
        except:
            return QtGui.QDialog()

    # -------------------------------------------------------------------------
    # Message API
    # -------------------------------------------------------------------------
    def message_critical(self, title, message, *args, **kwargs):
        """ Shortcut to display a critical popup dialog.

        """
        log.critical(message)
        return QtWidgets.QMessageBox.critical(self.window, "{0} - {1}".format(
            self.app_name, title), message, *args, **kwargs)

    def message_warning(self, title, message, *args, **kwargs):
        """ Shortcut to display a warning popup dialog.

        """
        log.warning(message)
        return QtWidgets.QMessageBox.warning(self.window, "{0} - {1}".format(
            self.app_name, title), message, *args, **kwargs)

    def message_information(self, title, message, *args, **kwargs):
        """ Shortcut to display an info popup dialog.

        """
        log.info(message)
        return QtWidgets.QMessageBox.information(self.window, "{0} - {1}".format(
            self.app_name, title), message, *args, **kwargs)

    def message_about(self, title, message, *args, **kwargs):
        """ Shortcut to display an about popup dialog.

        """
        log.info(message)
        return QtWidgets.QMessageBox.about(self.window, "{0} - {1}".format(
            self.app_name, title), message, *args, **kwargs)

    def message_question(self, title, message, *args, **kwargs):
        """ Shortcut to display a question popup dialog.

        """
        log.info(message)
        return QtWidgets.QMessageBox.question(self.window, "{0} - {1}".format(
            self.app_name, title), message, *args, **kwargs)

    # -------------------------------------------------------------------------
    # Workbench API
    # -------------------------------------------------------------------------
    def run(self):
        """ Run the UI workbench application.

        This method will load the core and ui plugins and start the
        main application event loop. This is a blocking call which
        will return when the application event loop exits.

        """
        InkcutWorkbench._instance = self

        with enaml.imports():
            from enaml.workbench.core.core_manifest import CoreManifest
            from enaml.workbench.ui.ui_manifest import UIManifest
            from inkcut.core.manifest import InkcutManifest
            #from inkcut.settings.manifest import SettingsManifest

        self.register(CoreManifest())
        self.register(UIManifest())
        self.register(InkcutManifest())
        #self.register(SettingsManifest())

        ui = self.get_plugin('enaml.workbench.ui')

        # Make sure ^C keeps working
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        #: Start the core plugin
        plugin = self.get_plugin('inkcut.core')
        self.set_language(plugin.language)

        ui.show_window()
        ui.start_application()
        #self.unregister('enaml.workbench.ui')

    def set_language(self, language):
        try:
            language = getattr(QtCore.QLocale, language, 'system')
            if isinstance(language, int):
                locale = QtCore.QLocale(language).name()
            elif callable(language):
                locale = language().name()
            else:
                locale = QtCore.QLocale.system().name()
            root_dir = os.path.dirname(os.path.dirname(__file__))
            path = os.path.join(root_dir, "res", "translations", locale)
            if self.translator.load(path):
                log.warning("Setting locale: %s" % locale)
                self.application._qapp.installTranslator(self.translator)
            else:
                log.warning("Translations not found at %s" % path)
        except Exception as e:
            log.exception(e)
