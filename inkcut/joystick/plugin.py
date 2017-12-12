# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 19, 2015

@author: jrm
"""
import functools
from atom.api import Instance, Int, observe
from enaml.qt import QtGui
from inkcut.core.api import Plugin
from inkcut.device.plugin import Device
from twisted.internet import defer


def with_connection(f):

    @functools.wraps(f)
    @defer.inlineCallbacks
    def wrapped(self, *args, **kwargs):
        device = self.device
        connected = device.connection.connected
        if not connected:
            yield defer.maybeDeferred(self.device.connect)

        #: Call original method
        f(self, *args, **kwargs)

        #if not connected:
        #    yield defer.maybeDeferred(self.device.disconnect)

    return wrapped 


class JoystickPlugin(Plugin):
    #: Reference to the inkcut.device plugin's device
    device = Instance(Device)

    #: Rate to moave
    rate = Int(10)
    path = Instance(QtGui.QPainterPath)

    #: Reference to the device plugin
    plugin = Instance(Plugin)

    def stop(self):
        """ Delete this plugins references """
        del self.device
        del self.plugin

    def _default_plugin(self):
        return self.workbench.get_plugin('inkcut.device')

    def _default_device(self):
        return self.plugin.device

    @observe('plugin.device')
    def _refresh_device(self, change):
        """ Whenever the device updates on the device plugin, update
        the local reference.
        """
        if self.device != change['value']:
            self.device = change['value']
            return
    #
    # @observe('device')
    # def _view_changed(self, change):
    #     view_items = []
    #     t = QtGui.QTransform.fromScale(1,-1)
    #
    #     self.path = QtGui.QPainterPath()#[#],QtGui.QPainterPath()]
    #     x,y,z = self.device.position
    #     r= max(10,self.device.blade_offset)#,self.device.blade_offset
    #     self.path.addEllipse(QtCore.QPointF(x,-y),r,r)
    #     #view_items.append(PainterPathPlotItem(self.paths[0],pen=self.pen_down))
    #     view_items.append(PainterPathPlotItem(self.path,pen=self.pen_down))
    #
    #
    #     if self.device:
    #         # Also observe any change to job.media and job.device
    #         view_items.append(PainterPathPlotItem(self.device.path*t,pen=self.pen_media,skip_autorange=True))
    #         view_items.append(PainterPathPlotItem(self.device.padding_path*t,pen=self.pen_media_padding,skip_autorange=True))
    #
    #     self.plot = view_items
    #     return view_items
    #
    # @observe('device.position')
    # def _position_changed(self,change):
    #     x0, y0, z0 = change['oldvalue']
    #     x1, y1, z1 = change['value']
    #
    #     self.path.translate(x1-x0, y0-y1) # Reverse y
    #     self.plot[0].updateData(self.path)

    def stop(self):
        if self.device:
            self.device.close()
            
    def set_origin(self):
        self.device.position = [0, 0, 0]

    @defer.inlineCallbacks
    def reconnect(self):
        yield self.device.connection.disconnect()
        yield self.device.connection.connect()
    
    @with_connection
    def move_to_origin(self):
        x, y, z = self.device.position
        self.device.move([0, 0, z], absolute=True)

    @with_connection
    def move_up(self):
        x, y, z = self.device.position
        self.device.move([0, self.rate, z], absolute=False)

    @with_connection
    def move_down(self):
        x, y, z = self.device.position
        self.device.move([0, -self.rate, z], absolute=False)

    @with_connection
    def move_left(self):
        x, y, z = self.device.position
        self.device.move([-self.rate, 0, z], absolute=False)

    @with_connection
    def move_right(self):
        x, y, z = self.device.position
        self.device.move([self.rate, 0, z], absolute=False)

    @with_connection
    def toggle_trigger(self):
        x, y, z = self.device.position
        z = 0 if z else 1
        self.device.move([0, 0, z], absolute=False)
