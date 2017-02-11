# -*- coding: utf-8 -*-
'''
Created on Jan 16, 2015

@author: jrm
'''
from atom.api import Float,Bool, Unicode,Int,ContainerList,observe
from inkcut.workbench.core.area import AreaBase

class Media(AreaBase):
    """ Model represnting the plot media """
    name = Unicode().tag(config=True)
    color = Unicode('#000000').tag(config=True)
    
    is_roll = Bool(False).tag(config=True)
    
    used = ContainerList(Float(),default=[0,0]).tag(config=True,help="amount used already (to determine available size)")
    cost = Float(1).tag(config=True,help="cost per square unit")
    
    use_force = Bool(False).tag(config=True)
    use_speed = Bool(False).tag(config=True)
    force = Int(10).tag(config=True)
    speed = Int(10).tag(config=True)
    
    def reset(self):
        self.used = (0.0,0.0)
        
    def unit_cost(self):
        return
