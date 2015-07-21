# -*- coding: utf-8 -*-
'''
Created on Jul 20, 2015

@author: jrm
'''
from atom.api import (Callable,Event, Value, Unicode, Bool, Instance,Typed, ForwardTyped, observe)
from enaml.core.declarative import d_
from enaml.widgets.control import Control, ProxyControl
from enaml.qt.qt_control import QtControl
from enaml.qt import QtCore

class ProxyKeyEvent(ProxyControl):
    declaration = ForwardTyped(lambda: KeyEvent)
    
    def set_enabled(self, enabled):
        raise NotImplementedError
    
class KeyEvent(Control):
    proxy = Typed(ProxyKeyEvent)
    
    key_code = d_(Value())
    key = d_(Unicode())
    enabled = d_(Bool(True))
    repeats = d_(Bool(True))
    
    pressed = d_(Event(),writable=False)
    released = d_(Event(),writable=False)
    
    @observe('enabled')
    def _update_proxy(self, change):
        """ An observer which sends state change to the proxy.
        """
        super(KeyEvent, self)._update_proxy(change)

class QtKeyEvent(QtControl, ProxyKeyEvent):
    _keyPressEvent = Callable() # Refs to original functions
    _keyReleaseEvent = Callable() # Refs to original functions
    widget = Instance(QtCore.QObject)
    
    def create_widget(self):
        self.widget = self.parent_widget()

    def init_widget(self):
        super(QtKeyEvent, self).init_widget()
        d = self.declaration
        widget = self.parent_widget()
        self._keyPressEvent = widget.keyPressEvent
        self._keyReleaseEvent = widget.keyPressEvent
        self.set_enabled(d.enabled)
    
    def set_enabled(self, enabled):
        widget = self.parent_widget()
        if enabled:
            widget.keyPressEvent = lambda event:self.on_key_press(event)
            widget.keyReleaseEvent = lambda event:self.on_key_release(event)
        else:
            # Restore original
            widget.keyPressEvent = self._keyPressEvent
            widget.keyReleaseEvent = self._keyReleaseEvent
            
    def on_key_press(self,event):
        try:
            if (self.declaration.key_code and event.key()==self.declaration.key_code) or \
                (self.declaration.key and self.declaration.key in event.text()):
                if not self.declaration.repeats and event.isAutoRepeat():
                    return
                self.declaration.pressed(event)
        finally:
            self._keyPressEvent(event)
        
    def on_key_release(self,event):
        try:
            if (self.declaration.key_code and event.key()==self.declaration.key_code) or \
                (self.declaration.key and self.declaration.key in event.text()):
                if not self.declaration.repeats and event.isAutoRepeat():
                    return
                self.declaration.released(event)
        finally:
            self._keyReleaseEvent(event)
        
def key_event_factory():
    return QtKeyEvent

# Inject the factory 
from enaml.qt.qt_factories import QT_FACTORIES
QT_FACTORIES['KeyEvent'] = key_event_factory