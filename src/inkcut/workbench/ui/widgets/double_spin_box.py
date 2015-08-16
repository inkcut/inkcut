# -*- coding: utf-8 -*-
'''
Created on Jun 11, 2015

@author: jrm
'''
from atom.api import (Float,  Typed, ForwardTyped)
from enaml.core.declarative import d_
from enaml.widgets.spin_box import ProxySpinBox, SpinBox
from enaml.qt.qt_spin_box import QtSpinBox
from enaml.qt.QtGui import QDoubleSpinBox

class ProxyDoubleSpinBox(ProxySpinBox):
    declaration = ForwardTyped(lambda: DoubleSpinBox)

class DoubleSpinBox(SpinBox):
    """ A spin box widget which manipulates float values.

    """
    #: The minimum value for the spin box. Defaults to 0.
    minimum = d_(Float(0))

    #: The maximum value for the spin box. Defaults to 100.
    maximum = d_(Float(100))
    
    #: The maximum value for the spin box. Defaults to 100.
    single_step = d_(Float(1.0))

    #: The position value of the spin box. The value will be clipped to
    #: always fall between the minimum and maximum.
    value = d_(Float(0))


class QtDoubleSpinBox(QtSpinBox, ProxyDoubleSpinBox):
    """ A Qt implementation of an Enaml SpinBox.

    """
    #: A reference to the widget created by the proxy.
    widget = Typed(QDoubleSpinBox)
    
    #--------------------------------------------------------------------------
    # Initialization API
    #--------------------------------------------------------------------------
    def create_widget(self):
        """ Create the underlying QDoubleSpinBox widget.

        """
        widget = QDoubleSpinBox(self.parent_widget())
        widget.setKeyboardTracking(False)
        self.widget = widget

def double_spin_box_factory():
    return QtDoubleSpinBox

# Inject the factory 
from enaml.qt.qt_factories import QT_FACTORIES
QT_FACTORIES['DoubleSpinBox'] = double_spin_box_factory