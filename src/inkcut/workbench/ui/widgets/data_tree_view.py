# -*- coding: utf-8 -*-
'''
Created on Jun 11, 2015

@author: jrm
'''
from atom.atom import set_default
from atom.api import (Callable, Instance,Typed, Enum,Float, Bool,ForwardTyped, observe)
from enaml.core.declarative import d_
from enaml.widgets.control import Control, ProxyControl
from enaml.qt.qt_control import QtControl
from pyqtgraph.widgets.DataTreeWidget import DataTreeWidget
from enaml.qt import QtGui

class ProxyDataTreeView(ProxyControl):
    declaration = ForwardTyped(lambda: DataTreeView)
    
    def set_data(self, data, hide_root=True):
        raise NotImplementedError

class DataTreeView(Control):
    hug_width = set_default('ignore')
    hug_height = set_default('ignore')
    proxy = Typed(ProxyDataTreeView)
    data = d_(Typed(object))
    hide_root = d_(Bool(True))
    selected = d_(Callable(lambda selected,deselected:None))
    selection_mode = d_(Enum(QtGui.QAbstractItemView.SingleSelection,QtGui.QAbstractItemView.MultiSelection,QtGui.QAbstractItemView.NoSelection))
    setup = d_(Callable(lambda parameter_tree:None))
    
    @observe('data')
    def _update_proxy(self, change):
        """ An observer which sends state change to the proxy.
        """
        # The superclass handler implementation is sufficient.
        super(DataTreeView, self)._update_proxy(change)    
        
    @observe('selected')            
    def _update_selected_callback(self,change):
        self.proxy.set_selection_callback(change['value'])
        
    @observe('selection_mode')            
    def _update_selection_mode_callback(self,change):
        self.proxy.set_selection_mode(change['value'])        

class QtDataTreeView(QtControl, ProxyDataTreeView):
    __weakref__ = None # Required for selection callbacks
    _selection_model = Instance(QtGui.QItemSelectionModel)
    widget = Typed(DataTreeWidget)
    def create_widget(self):
        self.widget = DataTreeWidget(self.parent_widget())

    def init_widget(self):
        super(QtDataTreeView, self).init_widget()
        d = self.declaration
        
        #self.widget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.set_data(d.data,d.hide_root)
        self.set_selection_callback(d.selected)
        self.set_selection_mode(d.selection_mode)
        d.setup(self.widget)

    def set_data(self, data,hide_root=True):
        self.widget.setData(data,hideRoot=hide_root)
    
    def set_selection_mode(self,mode):
        if not mode:
            mode = QtGui.QAbstractItemView.SingleSelection
        self.widget.setSelectionMode(mode)
    
    def set_selection_callback(self,callback):
        def safe_callback(selected,deselected):
            return callback(selected,deselected)
        self._selection_model = self.widget.selectionModel()
        self._selection_model.selectionChanged.connect(safe_callback)

def data_tree_view_factory():
    return QtDataTreeView

# Inject the factory 
from enaml.qt.qt_factories import QT_FACTORIES
QT_FACTORIES['DataTreeView'] = data_tree_view_factory