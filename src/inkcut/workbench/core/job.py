# -*- coding: utf-8 -*-
'''
Created on Jan 17, 2015

@author: jrm
'''
from __future__ import division
import os
import numpy as np
from atom.api import Enum,Float,Int,Bool,Instance,ContainerList,Unicode,observe
from enaml.qt import QtGui, QtCore
from inkcut.workbench.core.utils import ConfigurableAtom
from inkcut.workbench.core.media import Media
from inkcut.workbench.core.device import Device
from inkcut.workbench.core.svg import QtSvgDoc

class Padding:
    LEFT = 0
    TOP = 1
    RIGHT = 2
    BOTTOM = 3

class JobError(Exception):
    pass

class Job(ConfigurableAtom):
    """ 
    Create a plot depending on the properties set. 
    Any property that is a traitlet will cause an update when the value is changed. 
    """
    
    media = Instance(Media) 
    device = Instance(Device)
    document = Unicode() # Path to document
    
    # Job properties
    size = ContainerList(Float(),default=[1,1])# TODO: hooookk
    scale = ContainerList(Float(),default=[1,1]).tag(config=True)
    auto_scale = Bool(False).tag(config=True,help="automatically scale if it's too big for the area")
    lock_scale = Bool(True).tag(config=True,help="automatically scale if it's too big for the area")
    
    mirror = ContainerList(Bool(),default=[False,False]).tag(config=True)
    align_center = ContainerList(Bool(),default=[False,False]).tag(config=True)
    
    rotation = Float(0).tag(config=True)
    auto_rotate = Bool(False).tag(config=True,help="automatically rotate if it saves space")
    
    copies = Int(1).tag(config=True)
    auto_copies = Bool(True).tag(config=True,help="always use a full stack")
    copy_spacing = ContainerList(Float(),default=[10,10]).tag(config=True)
    copy_weedline = Bool(False).tag(config=True)
    copy_weedline_padding = ContainerList(Float(),default=[10,10,10,10]).tag(config=True)
    
    plot_weedline = Bool(False).tag(config=True)
    plot_weedline_padding = ContainerList(Float(),default=[10,10,10,10]).tag(config=True)
    
    order = Enum('Normal','Reversed').tag(config=True)
    
    feed_to_end = Bool(True).tag(config=True)
    feed_after = Float(0).tag(config=True)
    
    stack_size = ContainerList(Int(),default=[0,0])
    
    path = Instance(QtGui.QPainterPath) # Original path
    model = Instance(QtGui.QPainterPath) # Copy using job properties
    
    _blocked = Bool(False)
    _desired_copies = Int(1) # required for auto copies
    
    def _default_device(self):
        plugin = self.workbench.get_plugin('inkcut.workbench.core')
        return plugin.device
    
    def _default_media(self):
        plugin = self.workbench.get_plugin('inkcut.workbench.core')
        return plugin.media
    
    def _observe_document(self,change):
        if self.document and os.path.exists(self.document):
            self.path = QtSvgDoc(self.document)
        
    def _create_copy(self):
        """ Creates a copy of the original graphic applying the given transforms """
        bbox = self.path.boundingRect()
        
        # Create the base copy
        t = QtGui.QTransform()
        
        t.scale(
            self.scale[0] * (self.mirror[0] and -1 or 1),
            self.scale[1] * (self.mirror[1] and -1 or 1),
        )
        
        # Rotate about center
        if self.rotation!=0:
            c = bbox.center()
            t.translate(-c.x(),-c.y())
            t.rotate(self.rotation)
            t.translate(c.x(),c.y())
        
        # Apply transform
        path = self.path * t
        
        if self.order=='Reversed':
            path = path.toReversed()
         
        # Add weedline to copy
        if self.copy_weedline:
            self._add_weedline(path, self.copy_weedline_padding)
        
        # If it's too big we have to scale it
        w,h = path.boundingRect().width(), path.boundingRect().height()
        available_area = self.media.available_area
        if w > available_area.width() or h > available_area.height():
            
            # If it's too big an auto scale is enabled, resize it to fit
            if not self.auto_scale:
                raise JobError("Image is too large to fit on the material")
            sx,sy = 1,1
            if w > available_area.width():
                sx = available_area.width() / w
            if h > available_area.height():
                sy = available_area.height() / h
            s = min(sx,sy) # Fit to the smaller of the two
            path = self.path * QtGui.QTransform.fromScale(s,s)
            
        # Move to bottom left
        p = path.boundingRect().bottomLeft()
        
        path = path * QtGui.QTransform.fromTranslate(-p.x(),-p.y())
        
        
        return path
    
    @observe('path','scale','auto_scale','lock_scale','mirror',
             'align_center','rotation','auto_rotate','copies','order',
             'copy_spacing','copy_weedline','copy_weedline_padding',
             'plot_weedline','plot_weedline_padding','feed_to_end','feed_after',
             'media','media.size','media.padding','auto_copies')
    def _job_changed(self,change):
        """ Recreate an instance of of the plot using the current settings """
        #self.log.debug("name=%s, old=%s, new=%s"%(name,old,new))
        if self._blocked:
            return
        
        if change['name']=='copies':
            self._desired_copies = self.copies
        
        #try:
        model = QtGui.QPainterPath()
        
        if not self.path:
            return
        
        path = self._create_copy()
        
        # Update size
        bbox = path.boundingRect()
        self.size = [bbox.width(),bbox.height()]
                 
        # Create copies
        c = 0
        points = self._copy_positions_iter(path)
        
        if self.auto_copies:
            self.stack_size = self._compute_stack_sizes(path)
            if self.stack_size[0]:
                copies_left = self.copies % self.stack_size[0]
                if copies_left: # not a full stack
                    try:
                        self._blocked = True
                        
                        self.copies = self._desired_copies
                        self.add_stack()
                        
                    finally:
                        self._blocked = False
        
        while c<self.copies:
            x,y = points.next()
            model.addPath(path * QtGui.QTransform.fromTranslate(x,-y))
            c+=1
            
        # Create weedline
        if self.plot_weedline:
            self._add_weedline(model, self.plot_weedline_padding)
        
        # Move to 0,0
        bbox = model.boundingRect()
        p = bbox.bottomLeft()
        tx,ty = -p.x(),-p.y()
        
        # Center or set to padding 
        tx += self.align_center[0] and (self.media.width()-bbox.width())/2.0 or self.media.padding_left
        ty += self.align_center[1] and -(self.media.height()-bbox.height())/2.0 or -self.media.padding_bottom
            
        t = QtGui.QTransform.fromTranslate(tx,ty)
        
        model= model * t
        
        end_point = self.feed_to_end and QtCore.QPointF(0,-self.feed_after+model.boundingRect().top()) or QtCore.QPointF(0,0)
        model.moveTo(end_point)
        
        # Set new model
        self.model = model#.simplified()
        #except:
        #    # Undo the change
        #    if 'oldvalue' in change:
        #        setattr(change['object'],change['name'],change['oldvalue'])
        #    raise
        #if not self.check_bounds(self.boundingRect(),self.available_area):
        #    raise JobError("Plot outside of plotting area, increase the area or decrease the scale or decrease number of copies!")
    
    def _check_bounds(self, plot, area):
        """ Checks that the width and height of plot are less than the width and height of area """
        return plot.width()>area.width() or plot.height() > area.height()
    
    def _copy_positions_iter(self,path,axis=0):
        """ Generator that creates positions of points"""
        other_axis = axis +1 % 2
        p = [0,0]
        
        bbox = path.boundingRect()
        d = (bbox.width(),bbox.height())
        pad = self.copy_spacing
        stack_size = self._compute_stack_sizes(path)
        
        while True:
            p[axis] = 0
            yield p # Beginning of each row
            
            for i in xrange(stack_size[axis]-1):
                p[axis] += d[axis]+pad[axis]
                yield p
            
            p[other_axis] += d[other_axis]+pad[other_axis]
            
    def _compute_stack_sizes(self,path):
        # Usable area
        a = [self.media.width(),self.media.height()]
        a[0] -= self.media.padding[Padding.LEFT] + self.media.padding[Padding.RIGHT]
        a[1] -= self.media.padding[Padding.TOP] + self.media.padding[Padding.BOTTOM]
        
        # Clone includes weedline but not spacing
        bbox = path.boundingRect()
        size = [bbox.width(),bbox.height()]
        
        stack_size = [0,0]
        p = [0,0]
        for i in xrange(2):
            # Compute stack
            while (p[i]+size[i])<a[i]: # while another one fits
                stack_size[i]+=1
                p[i] += size[i]+self.copy_spacing[i] # Add only to end
        
        self.stack_size = stack_size
        return stack_size
        
    
    def _add_weedline(self,path,padding):
        """ Adds a weedline to the path 
        by creating a box around the path with the given padding
        """
        bbox = path.boundingRect()
        w,h = bbox.width(),bbox.height()
             
        tl = bbox.topLeft()
        x = tl.x() - padding[Padding.LEFT]
        y = tl.y() - padding[Padding.TOP]
        
        w += padding[Padding.LEFT] + padding[Padding.RIGHT]
        h += padding[Padding.TOP] + padding[Padding.BOTTOM]
        
        path.addRect(x,y,w,h)
        return path
    
    @property
    def state(self):
        pass
    
    @property
    def move_path(self):
        """ Returns the path the head moves when not cutting """
        # Compute the negative
        path = QtGui.QPainterPath()
        for i in range(self.model.elementCount()):
            e = self.model.elementAt(i)
            if e.isMoveTo():
                path.lineTo(e.x,e.y)
            else:
                path.moveTo(e.x,e.y)
        return path
    
    @property        
    def cut_path(self):
        """ Returns path where it is cutting """
        return self.model
    
    @property
    def offset_path(self):
        """ Returns path where it is cutting """
        path = QtGui.QPainterPath()
        _p = QtCore.QPointF(0,0) # previous point
        step = 0.1
        for subpath in QtSvgDoc.toSubpathList(self.model):#.toSubpathPolygons():
            e = subpath.elementAt(0)
            path.moveTo(QtCore.QPointF(e.x,e.y))
            length = subpath.length()
            distance = 0
            while distance<=length:
                t = subpath.percentAtLength(distance)
                p = subpath.pointAtPercent(t)
                a = subpath.angleAtPercent(t)+90
                #path.moveTo(p)#QtCore.QPointF(x,y))
                x = p.x()+np.multiply(self.device.blade_offset,np.sin(np.deg2rad(a)))
                y = p.y()+np.multiply(self.device.blade_offset,np.cos(np.deg2rad(a)))
                path.lineTo(QtCore.QPointF(x,y))
                distance+=step
            #_p = p # update last
            
        return path
    
    def add_stack(self):
        """ Add a complete stack or fill the row """
        copies_left = self.stack_size[0]-(self.copies % self.stack_size[0])
        if copies_left == 0: # Add full stack
            self.copies = self.copies + self.stack_size[0]
        else: # Fill stack
            self.copies = self.copies+copies_left
    
    def remove_stack(self):
        """ Remove a complete stack or the rest of the row """
        if self.copies<=self.stack_size[0]:
            self.copies = 1
            return
        
        copies_left = self.copies % self.stack_size[0] 
        if copies_left == 0: # Add full stack
            self.copies = self.copies - self.stack_size[0]
        else: # Fill stack
            self.copies = self.copies - copies_left
    
    
    
    def clone(self):
        """ Return a cloned instance of this object """
        clone = Job(**self.members())
        return clone
        
        
