# -*- coding: utf-8 -*-
'''
Created on Jul 20, 2015

@author: jrm
'''
from atom.api import (Event, Unicode, Bool, Typed, ForwardTyped, observe)
from enaml.core.declarative import d_
from enaml.widgets.control import Control, ProxyControl
from enaml.qt.qt_control import QtControl
from enaml.qt.QtGui import QShortcut
from enaml.qt import QtGui


class ProxyShortcut(ProxyControl):
    declaration = ForwardTyped(lambda: Shortcut)
    
    def set_key(self, key):
        raise NotImplementedError
    
    def set_enabled(self, enabled):
        raise NotImplementedError
    
    def set_repeat(self, repeat):
        raise NotImplementedError
    
    def set_whats_this(self, text):
        raise NotImplementedError

class Shortcut(Control):
    proxy = Typed(ProxyShortcut)
    
    key = d_(Unicode())
    enabled = d_(Bool(True))
    whats_this = d_(Unicode())
    repeat = d_(Bool())
    
    triggered = d_(Event(),writable=False)
    
    @observe('key','enabled','whats_this','repeat')
    def _update_proxy(self, change):
        """ An observer which sends state change to the proxy.
        """
        super(Shortcut, self)._update_proxy(change)

class QtShortcut(QtControl, ProxyShortcut):
    widget = Typed(QShortcut)
    def create_widget(self):
        self.widget = QShortcut(self.parent_widget())

    def init_widget(self):
        super(QtShortcut, self).init_widget()
        d = self.declaration
        self.set_key(d.key)
        self.set_enabled(d.enabled)
        if d.whats_this:
            self.set_whats_this(d.text)
        self.set_repeat(d.repeat)
        self.widget.activated.connect(self.on_activated)
    
    def on_activated(self,event):   
        self.declaration.triggered(event)
        
    def set_key(self, key):
        self.widget.setKey(QtGui.QKeySequence(key))
        
    def set_enabled(self, enabled):
        self.widget.setEnabled(enabled)
        
    def set_whats_this(self, text):
        self.widget.setWhatsThis(text)
        
    def set_repeat(self, repeat):
        self.widget.setAutoRepeat(repeat)

def shortcut_factory():
    return QtShortcut

# Inject the factory 
from enaml.qt.qt_factories import QT_FACTORIES
QT_FACTORIES['Shortcut'] = shortcut_factory