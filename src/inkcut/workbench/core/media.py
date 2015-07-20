# -*- coding: utf-8 -*-
'''
Created on Jan 16, 2015

@author: jrm
'''
from atom.api import Float,Bool, Instance,Unicode,Int,ContainerList,observe
from enaml.qt import QtCore, QtGui
from inkcut.workbench.core.utils import ConfigurableAtom

class Media(ConfigurableAtom):
    """ Model represnting the plot media """
    name = Unicode().tag(config=True)
    color = Unicode('#000000').tag(config=True)
    
    size = ContainerList(Float(),default=[1800,2700]).tag(config=True)
    padding = ContainerList(Float(),default=[10,10,10,10]).tag(config=True) # Left, Top, Right, Bottom
    is_roll = Bool(False).tag(config=True)
    
    used = ContainerList(Float(),default=[0,0]).tag(config=True,help="amount used already (to determine available size)")
    cost = Float(1).tag(config=True,help="cost per square unit")
    
    use_force = Bool(False).tag(config=True)
    use_speed = Bool(False).tag(config=True)
    force = Int(10).tag(config=True)
    speed = Int(10).tag(config=True)
    
    model = Instance(QtCore.QRectF,())
    
        
    @observe('size','padding')
    def _sync_size(self,change):
        self.model.setWidth(self.size[0]-self.used[0])
        self.model.setHeight(self.size[1]-self.used[1])
        
    @property
    def padding_left(self):
        return self.padding[0]
    
    @property
    def padding_top(self):
        return self.padding[1]
    
    @property
    def padding_right(self):
        return self.padding[2]
    
    @property
    def padding_bottom(self):
        return self.padding[3]
        
    @property
    def area(self):
        return self.model
    
    def width(self):
        return self.size[0]
    
    def height(self):
        return self.size[1]
    
    
    @property
    def available_area(self):
        x,y = self.padding_left,self.padding_bottom
        w,h = self.size[0]-(self.padding_right+self.padding_left),self.size[1]-(self.padding_bottom+self.padding_top)
        return QtCore.QRectF(x,y,w,h)
        
    def reset(self):
        self.used = (0.0,0.0)
        
    @property
    def path(self):
        media = QtGui.QPainterPath()
        media.addRect(self.area)
        return media
        
    @property
    def padding_path(self):
        # Add a box around the plot
        # Show plot area
        media_padding = QtGui.QPainterPath()
        media_padding.addRect(self.available_area)
        return media_padding
        
    
        
        
# class MediaListModel(LoggingConfigurable,QtCore.QAbstractListModel):
#     class MediaListModelMeta(type(LoggingConfigurable),type(QtCore.QAbstractListModel)):
#         pass
#     __metaclass__ = MediaListModelMeta
#     
#     headers = List(['Media'])
#     items = List(Dict,[])
#     
#     def __init__(self,**kwargs):
#         LoggingConfigurable.__init__(self,**kwargs)
#         QtCore.QAbstractListModel.__init__(self)
#     
#     def data(self, index, role):
#         if not index.isValid():
#             return
#         elif role==QtCore.Qt.DisplayRole:
#             return self.items[index.row()]['name']
#         
#     def rowCount(self,parent=None):
#         return len(self.items)
#     
#     
# class ManageMediaDialog(LoggingConfigurable,QtGui.QDialog):
#     class ManageMediaDialogMeta(type(LoggingConfigurable),type(QtGui.QDialog)):
#         pass
#     __metaclass__ = ManageMediaDialogMeta
#     
#     media = List(Dict,[{'name':'test'},{'name':'New item'}],config=True,help="list of media")
#     current_media = Instance(Media,(),dict(name="New"))
#         
#     def __init__(self,parent=None,**kwargs):
#         QtGui.QDialog.__init__(self,parent)
#         LoggingConfigurable.__init__(self,**kwargs)
#         
#         
#         self.init_ui()
#         self.init_model()
#         self.init_signals()
#         
#         self.current_media = Media()
#     
#     def init_ui(self):
#         self.ui = Ui_Dialog()
#         self.ui.setupUi(self)
#         self.setWindowTitle("Media Manager - %s"%self.app.window_name)
#         
#     def init_model(self):
#         self.ui.listView.setModel(MediaListModel(items=self.media))
#         
#         def load_media(new,old):
#             """ Update media when selection changes """
#             if not new.count():
#                 return
#             index = new.first().indexes()[0]
#             if not index.isValid():
#                 return
#             try:
#                 model = self.ui.listView.model()
#                 self.current_media = Media(config=Config(model.items[index.row()]))
#                 # Not sure why i have to do this...
#                 self._current_media_changed()
#             except:
#                 self.log.error(traceback.format_exc())
#             
#         self.ui.listView.selectionChanged = load_media
#     
#     def init_signals(self):
#         self._trait_signal_handlers = {}
#         for widget,signal,prop in (
#                (self.ui.lineEditName,'editingFinished','name'),
#                 (self.ui.checkBoxForce,'toggled','use_force'),
#                 (self.ui.checkBoxSpeed,'toggled','use_speed'),
#                 (self.ui.checkBoxIsRoll,'toggled','is_roll'),
#                 (self.ui.doubleSpinBoxCost,'valueChanged','cost'),
#                 (self.ui.doubleSpinBoxForce,'valueChanged','force'),
#                 (self.ui.doubleSpinBoxSpeed,'valueChanged','speed'),
#                 (self.ui.doubleSpinBoxHeight,'valueChanged','height'),
#                 (self.ui.doubleSpinBoxWidth,'valueChanged','width'),
#             ):
#             signal = getattr(widget,signal)
#             signal.connect(self._bind_ui_value_to_media_trait)
#             self._trait_signal_handlers[widget] = prop
#             
#     def _current_media_changed(self):
#         """ When a different media is selected load the properties """
#         if self.current_media is None:
#             return
#         self.log.debug("Changed!")
#         self._block_signals(True)
#         try:
#             self.ui.lineEditName.setText(self.current_media.name)
#             
#             self.ui.checkBoxIsRoll.setChecked(self.current_media.is_roll)
#             self.ui.doubleSpinBoxHeight.setValue(self.current_media.size_x)
#             self.ui.doubleSpinBoxWidth.setValue(self.current_media.size_y)
#             
#             self.ui.checkBoxForce.setChecked(self.current_media.use_force)        
#             self.ui.checkBoxSpeed.setChecked(self.current_media.use_speed)
#             self.ui.doubleSpinBoxForce.setValue(self.current_media.force)
#             self.ui.doubleSpinBoxSpeed.setValue(self.current_media.speed)
#             
#             self.ui.doubleSpinBoxCost.setValue(self.current_media.cost)
#         finally:
#             self._block_signals(False)
#             
#     def _block_signals(self,blocked):
#         """ Make sure when loading that no events are fired """
#         for w in [self.ui.lineEditName,
#                   self.ui.checkBoxForce,
#                   self.ui.checkBoxSpeed,
#                   self.ui.checkBoxIsRoll,
#                   self.ui.doubleSpinBoxCost,
#                   self.ui.doubleSpinBoxForce,
#                   self.ui.doubleSpinBoxSpeed,
#                   self.ui.doubleSpinBoxHeight,
#                   self.ui.doubleSpinBoxWidth]:
#             w.blockSignals(blocked)
#     
#     def _bind_ui_value_to_media_trait(self,v):
#         """ callback that binds the UI value to trait value so they stay in sync """
#         src = self.sender()
#         trait = self._trait_signal_handlers[src]
#         obj = self.current_media
#         
#         if not obj:
#             return
#         
#         if isinstance(src, QtGui.QDoubleSpinBox):
#             u = src.suffix().strip()
#             if u in QtSvgDoc._uuconv.keys():
#                 # Format to user units
#                 v = QtSvgDoc.parseUnit('%s%s'%(v,u))
#         
#         # Incase something bad happens...
#         old = getattr(obj,trait)
#         try:
#             setattr(obj,trait,v)
#         except:
#             setattr(obj,trait,old)
#             raise
#         
        