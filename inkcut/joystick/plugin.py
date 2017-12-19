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
from inkcut.core.api import Plugin
from inkcut.device.plugin import Device
from twisted.internet import defer
from enaml.qt import QtCore, QtGui


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

    #: Rate to move
    rate = Int(100).tag(config=True)
    path = Instance(QtGui.QPainterPath)

    #: Reference to the device plugin
    plugin = Instance(Plugin)

    def stop(self):
        """ Delete this plugins references """
        if self.device:
            self.device.close()
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

    def set_origin(self):
        """ Update the origin and clear the position """
        self.device.origin = self.device.position
        #self.device.position = [0, 0, 0]

    @defer.inlineCallbacks
    def reconnect(self):
        yield self.device.connection.disconnect()
        yield self.device.connection.connect()
    
    @with_connection
    def move_to_origin(self, system=False):
        x, y, z = [0, 0, 0] if system else self.device.origin
        self.device.move([x, y, 0], absolute=True)

    @with_connection
    def move_up(self):
        x, y, z = self.device.position
        self.device.move([x, y+self.rate, z], absolute=True)

    @with_connection
    def move_down(self):
        x, y, z = self.device.position
        self.device.move([x, y-self.rate, z], absolute=True)

    @with_connection
    def move_left(self):
        x, y, z = self.device.position
        self.device.move([x-self.rate, y, z], absolute=True)

    @with_connection
    def move_right(self):
        x, y, z = self.device.position
        self.device.move([x+self.rate, y, z], absolute=True)

    @with_connection
    def move_head_up(self):
        x, y, z = self.device.position
        self.device.move([x, y, 0], absolute=True)

    @with_connection
    def move_head_down(self):
        x, y, z = self.device.position
        self.device.move([x, y, 1], absolute=True)
