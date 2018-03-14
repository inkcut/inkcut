"""
Copyright (c) 2018, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Mar 14, 2018

@author: jrm
"""
from threading import Timer


def close():
    from inkcut.core.workbench import InkcutWorkbench
    wb = InkcutWorkbench.instance()
    core = wb.get_plugin("enaml.workbench.core")
    core.invoke_command('enaml.workbench.ui.close_window')


def test_app():
    # Must close programatically
    Timer(10, close).start()
    from inkcut.app import main
    main()

