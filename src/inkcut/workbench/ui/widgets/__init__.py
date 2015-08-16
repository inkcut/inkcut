_installed = [False]

def install_qt_dialog_hack():
    # Hack the QDialog
    from atom.catom import atomref
    from enaml.qt.qt_dialog import QWindowDialog
    from enaml.qt.q_window_base import QWindowLayout,QLayout,QSize,Qt

    def __init__(self, proxy, parent=None, flags=Qt.Widget):
        """ Initialize a QWindowDialog.
    
        Parameters
        ----------
        proxy : QtDialog
            The proxy object which owns this dialog. Only an atomref
            will be maintained to this object.
    
        parent : QWidget, optional
            The parent of the dialog.
    
        flags : Qt.WindowFlags, optional
            The window flags to pass to the parent constructor.
    
        """
        super(QWindowDialog, self).__init__(parent, flags)
        self._proxy_ref = atomref(proxy)
        
        # Hack for PySide
        if not self.layout():
            self._expl_min_size = QSize()
            self._expl_max_size = QSize()
            layout = QWindowLayout()
            layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
            self.setLayout(layout)
            
    QWindowDialog.__init__ = __init__
    _installed[0] = True

if not _installed[0]:
    install_qt_dialog_hack()