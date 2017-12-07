# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import enamlx
enamlx.install()
from inkcut.workbench.core.app import InkcutWorkbench

if __name__ == '__main__':
    workbench = InkcutWorkbench()
    workbench.run() 
