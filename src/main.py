# -*- coding: utf-8 -*-
'''
Created on Jul 12, 2015

@author: jrm
'''
import os
import sys
#sys.path.append('../')
print (os.getcwd(), sys.path)

from inkcut.workbench.core.app import InkcutWorkbench

if __name__ == '__main__':
    workbench = InkcutWorkbench()
    workbench.run() 
