"""
Copyright (c) 2018, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Mar 14, 2018

@author: jrm
"""
import os
import subprocess
import sys

import pytest
from threading import Timer
from enaml.application import deferred_call

try:
    import pyqtgraph
    is_pyqtgraph_available = True
except:
    is_pyqtgraph_available = False


def close():
    from inkcut.core.workbench import InkcutWorkbench
    wb = InkcutWorkbench.instance()
    core = wb.get_plugin("enaml.workbench.core")
    core.invoke_command('enaml.workbench.ui.close_window')


@pytest.mark.skipif(not is_pyqtgraph_available,
                    reason='pyqtgraph is not available')
def test_app():
    # Must close programatically
    Timer(10, lambda: deferred_call(close)).start()
    from inkcut.app import main
    main()


def test_application_names_its_window_class():
    """The dock raises a window by its class. Qt reads that once, from argv."""
    code = (
        "import enaml\n"
        "with enaml.imports():\n"
        "    from inkcut.core.manifest import application_factory\n"
        "app = application_factory()\n"
        "qapp = app._qapp\n"
        "assert list(qapp.arguments())[:1] == ['inkcut'], list(qapp.arguments())\n"
        "assert qapp.applicationName() == 'inkcut'\n"
        "assert qapp.desktopFileName() == 'inkcut'\n"
    )
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    proc = subprocess.run(
        [sys.executable, '-c', code],
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

