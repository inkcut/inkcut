# -*- coding: utf-8 -*-
'''
Created on Jul 19, 2015

@author: jrm
'''
from atom.api import Instance,Int
from inkcut.workbench.core.utils import Plugin
from inkcut.workbench.core.device import Device
from inkcut.workbench.ui.plugin import PlotBase


class JoystickPlugin(Plugin,PlotBase):
    
    device = Instance(Device)
    rate = Int(10)
    
    def start(self):
        pass
    
    def _observe_device(self,change):
            self.device.init()
        
    def stop(self):
        if self.device:
            self.device.close()
    
    def move_up(self):
        x,y,z = self.device.position
        self.device.move(x,y+self.rate,z)
    
    def move_down(self):
        x,y,z = self.device.position
        self.device.move(x,y-self.rate,z)
    
    def move_left(self):
        x,y,z = self.device.position
        self.device.move(x-self.rate,y,z)
    
    def move_right(self):
        x,y,z = self.device.position
        self.device.move(x+self.rate,y,z)
    
    def toggle_trigger(self):
        x,y,z = self.device.position
        if z:
            z = 0
        else:
            z = 1
        self.device.move(x,y,z)