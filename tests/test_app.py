"""
Copyright (c) 2018, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Mar 14, 2018

@author: jrm
"""
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

