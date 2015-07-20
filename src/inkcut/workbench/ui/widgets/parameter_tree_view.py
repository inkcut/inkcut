# -*- coding: utf-8 -*-
'''
Created on Jun 11, 2015

@author: jrm
'''
from atom.atom import set_default
from atom.api import (Callable, Typed, ForwardTyped, observe)
from enaml.core.declarative import d_
from enaml.widgets.control import Control, ProxyControl
from enaml.qt.qt_control import QtControl
from pyqtgraph.parametertree.Parameter import Parameter
from pyqtgraph.parametertree.ParameterTree import ParameterTree


class ProxyParameterTreeView(ProxyControl):
    declaration = ForwardTyped(lambda: ParameterTreeView)
    
    def set_params(self, params):
        raise NotImplementedError

class ParameterTreeView(Control):
    hug_width = set_default('ignore')
    hug_height = set_default('ignore')
    proxy = Typed(ProxyParameterTreeView)
    params = d_(Typed(Parameter))
    setup = d_(Callable(lambda parameter_tree:None))
    
    @observe('params')
    def _update_proxy(self, change):
        """ An observer which sends state change to the proxy.
        """
        # The superclass handler implementation is sufficient.
        super(ParameterTreeView, self)._update_proxy(change)    

class QtParameterTreeView(QtControl, ProxyParameterTreeView):
    widget = Typed(ParameterTree)
    def create_widget(self):
        self.widget = ParameterTree(self.parent_widget())

    def init_widget(self):
        super(QtParameterTreeView, self).init_widget()
        d = self.declaration
        #self.widget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.set_params(d.params)
        d.setup(self.widget)

    def set_params(self, params):
        self.widget.setParameters(params,showTop=False)

def parameter_tree_view_factory():
    return QtParameterTreeView

# Inject the factory 
from enaml.qt.qt_factories import QT_FACTORIES
QT_FACTORIES['ParameterTreeView'] = parameter_tree_view_factory