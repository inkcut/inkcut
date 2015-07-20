# -*- coding: utf-8 -*-
'''
Created on Jun 11, 2015

@author: jrm
'''
from atom.atom import set_default
from atom.api import (Callable, ContainerList, Int, Unicode, Bool, Typed, ForwardTyped, observe)
from enaml.core.declarative import d_
from enaml.widgets.control import Control, ProxyControl
from enaml.qt.qt_control import QtControl
from pyqtgraph.widgets.TableWidget import TableWidget
from enaml.qt.QtGui import QSizePolicy


class ProxyArrayTableView(ProxyControl):
    declaration = ForwardTyped(lambda: ArrayTableView)
    
    def set_data(self, data):
        raise NotImplementedError
    
    def append_data(self, data):
        raise NotImplementedError

class ArrayTableView(Control):
    hug_width = set_default('ignore')
    hug_height = set_default('ignore')
    proxy = Typed(ProxyArrayTableView)
    
    data = d_(ContainerList())
    auto_scroll = d_(Bool(False))
    stretch_last_section = d_(Bool(False))
    sortable = d_(Bool(False))
    sort_column = d_(Int(0))
    sort_mode = d_(Unicode('index'))
    setup = d_(Callable(lambda array_table:None))
    
    # Callbacks
    selected = d_(Callable(lambda selected,deselected:None))
    
    
    @observe('data')
    def _update_proxy(self, change):
        """ An observer which sends state change to the proxy.
        """
        if change['type'] == 'update' and self.proxy_is_active:
            if not change['oldvalue']:
                handler = getattr(self.proxy, 'set_' + change['name'], None)
                if handler is not None:
                    handler(change['value'])
            else:
                handler = getattr(self.proxy, 'append_' + change['name'], None)
                if handler is not None:
                    handler(change['value'][len(change['oldvalue']):-1])
    
    @observe('sortable','sort_column','sort_mode')            
    def _update_sorting(self,change):
        self.proxy.widget.setSortingEnabled(self.sortable)
        self.proxy.widget.setSortMode(self.sort_column,self.sort_mode)
        
    @observe('stretch_last_section')            
    def _update_resize(self,change):
        self.proxy.widget.horizontalHeader().setStretchLastSection(self.stretch_last_section)
        
    @observe('selected')            
    def _update_selected_callback(self,change):
        self.proxy.set_selection_callback(change['value'])
        

class QtArrayTableView(QtControl, ProxyArrayTableView):
    __weakref__ = None # Required for selection callbacks
    widget = Typed(TableWidget)
    def create_widget(self):
        self.widget = TableWidget(self.parent_widget())

    def init_widget(self):
        super(QtArrayTableView, self).init_widget()
        d = self.declaration
        self.widget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.widget.setSortingEnabled(d.sortable)
        self.widget.horizontalHeader().setStretchLastSection(d.stretch_last_section)
        self.set_selection_callback(d.selected)
        self.set_data(d.data)
        d.setup(self.widget)
        
    def set_selection_callback(self,callback):
        def safe_callback(selected,deselected):
            return callback(selected,deselected)
        m = self.widget.selectionModel()
        m.selectionChanged.connect(safe_callback)

    def set_data(self, data):
        self.widget.setData(data)
        
    def append_data(self, data):
        self.widget.appendData(data)
        if self.declaration.auto_scroll:
            self.widget.scrollToBottom()

def array_table_view_factory():
    return QtArrayTableView

# Inject the factory 
from enaml.qt.qt_factories import QT_FACTORIES
QT_FACTORIES['ArrayTableView'] = array_table_view_factory