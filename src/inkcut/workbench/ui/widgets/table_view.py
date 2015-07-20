# -*- coding: utf-8 -*-
'''
Created on Jun 9, 2015

@author: jrm
'''
from atom.atom import set_default
from atom.api import (Atom,ContainerList,Bool,Instance,Float,ForwardInstance,Callable, Enum, Typed, ForwardTyped, observe)
from enaml.core.declarative import d_
from enaml.widgets.control import Control, ProxyControl
from enaml.qt.qt_control import QtControl
from enaml.qt.QtCore import (QAbstractTableModel,Qt)
from enaml.qt.QtGui import QTableView, QSizePolicy
from enaml.qt import QtGui
import time

class AtomTableModel(Atom):
    headers = ContainerList()
    items = ContainerList()
    model = ForwardInstance(lambda:AtomQtTableModel)
    
    def _default_model(self):
        return AtomQtTableModel(model=self)
    
    @observe('items','headers')
    def _items_updated(self,change):
        self.model.layoutChanged.emit()
        #self.model.
        #self.widget.scrollToBottom()
     

class AtomQtTableModel(QAbstractTableModel):
    def __init__(self,model=None,**kwargs):
        self.model = model or AtomTableModel()
        QAbstractTableModel.__init__(self,**kwargs)
        #self.sc
        
    def rowCount(self, parent=None):
        return len(self.model.items)
    
    def columnCount(self, parent=None):
        return len(self.model.headers)
    
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return getattr(self.model.items[index.row()],self.model.headers[index.column()][1])
    
    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.model.headers[col][0]
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return col
        return None
    


class ProxyTableView(ProxyControl):
    declaration = ForwardTyped(lambda: TableView)
    
    def set_model(self, model):
        raise NotImplementedError

class TableView(Control):
    hug_width = set_default('ignore')
    hug_height = set_default('ignore')
    proxy = Typed(ProxyTableView)
    model = d_(Typed(QAbstractTableModel))
    auto_scroll = d_(Bool(True))
    stretch_last_section = d_(Bool(False))
    selected = d_(Callable(lambda selected,deselected:None))
    selection_mode = d_(Enum(QtGui.QAbstractItemView.SingleSelection,QtGui.QAbstractItemView.MultiSelection,QtGui.QAbstractItemView.NoSelection))
    
    setup = d_(Callable(lambda table_view:None))
    
    @observe('model')
    def _update_proxy(self, change):
        """ An observer which sends state change to the proxy.
        """
        # The superclass handler implementation is sufficient.
        super(TableView, self)._update_proxy(change)
        
    @observe('stretch_last_section')            
    def _update_resize(self,change):
        self.proxy.widget.horizontalHeader().setStretchLastSection(self.stretch_last_section)
        
    @observe('selected')            
    def _update_selected_callback(self,change):
        self.proxy.set_selection_callback(change['value'])    

class QtTableView(QtControl, ProxyTableView):
    __weakref__ = None # Required for selection callbacks
    _selection_model = Instance(QtGui.QItemSelectionModel)
    widget = Typed(QTableView)
    def create_widget(self):
        self.widget = QTableView(self.parent_widget())

    def init_widget(self):
        super(QtTableView, self).init_widget()
        d = self.declaration
        self.widget.setSortingEnabled(False)
        self.widget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.widget.horizontalHeader().setStretchLastSection(d.stretch_last_section)
        self.set_model(d.model)
        self.set_selection_callback(d.selected)
        self.set_selection_mode(d.selection_mode)
        d.setup(self.widget)
        
    def set_selection_callback(self,callback):
        def safe_callback(selected,deselected):
            return callback(selected,deselected)
            
        self._selection_model = self.widget.selectionModel()
        self._selection_model.selectionChanged.connect(safe_callback)
        
    def set_selection_mode(self,mode):
        if not mode:
            mode = QtGui.QAbstractItemView.SingleSelection
        self.widget.setSelectionMode(mode)

    def set_model(self, model):
        self.widget.setModel(model)
        model.layoutChanged.connect(self._on_layout_changed)
    
    def _on_layout_changed(self,*args,**kwargs):
        self.auto_scroll()
    
    def auto_scroll(self):
        if self.declaration.auto_scroll:
            self.widget.scrollToBottom()    

def table_view_factory():
    return QtTableView

# Inject the factory 
from enaml.qt.qt_factories import QT_FACTORIES
QT_FACTORIES['TableView'] = table_view_factory