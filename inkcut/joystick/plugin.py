# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 19, 2015

@author: jrm
"""
import functools
from contextlib import asynccontextmanager
from atom.api import Instance, Int, observe
from enaml.qt import QtCore, QtGui


from inkcut.core.api import Plugin
from inkcut.device.plugin import Device


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

    async def reconnect(self):
        await self.device.connection.disconnect()
        await self.device.connection.connect()

    @asynccontextmanager
    async def connected_device(self):
        device = self.device
        connected = device.connection.connected
        if not connected:
            await device.connect()
        yield device

    async def move_to_origin(self, system=False):
        async with self.connected_device() as device:
            x, y, z = [0, 0, 0] if system else device.origin
            await device.move([x, y, 0], absolute=True)

    async def move_up(self):
        async with self.connected_device() as device:
            x, y, z = device.position
            await device.move([x, y+self.rate, z], absolute=True)

    async def move_down(self):
        async with self.connected_device() as device:
            x, y, z = device.position
            await device.move([x, y-self.rate, z], absolute=True)

    async def move_left(self):
        async with self.connected_device() as device:
            x, y, z = device.position
            await device.move([x-self.rate, y, z], absolute=True)

    async def move_right(self):
        async with self.connected_device() as device:
            x, y, z = device.position
            await device.move([x+self.rate, y, z], absolute=True)

    async def move_head_up(self):
        async with self.connected_device() as device:
            x, y, z = device.position
            await device.move([x, y, 0], absolute=True)

    async def move_head_down(self):
        async with self.connected_device() as device:
            x, y, z = device.position
            await device.move([x, y, 1], absolute=True)
