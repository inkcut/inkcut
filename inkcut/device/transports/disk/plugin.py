# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Mar 13, 2018

@author: jrm
"""
import os
import time
import tempfile
from os.path import join, exists
from atom.atom import set_default
from atom.api import Instance, Unicode
from inkcut.core.api import Plugin, Model, log
from inkcut.device.plugin import DeviceTransport


class FileConfig(Model):
    format = Unicode("inkcut-{time}.{protocol}")
    directory = Unicode()

    def _default_directory(self):
        return tempfile.gettempdir()


class FileTransport(DeviceTransport):

    #: Default config
    config = Instance(FileConfig, ())

    #: The OS spools file writes
    always_spools = set_default(True)

    #: The output buffer
    file = Instance(object)

    def connect(self):
        config = self.config
        params = dict(
            time=str(time.time()).split(".")[0],
            protocol=str(self.protocol.declaration.id).lower()
        )
        path = join(config.directory, config.format.format(**params))
        if not exists(config.directory):
            os.makedirs(config.directory)
        log.debug("-- File | Writing to '{}'".format(path))
        self.file = open(path, 'wb')
        self.connected = True
        #: Save a reference
        self.protocol.transport = self
        self.protocol.connection_made()

    def write(self, data):
        log.debug("-> File | {}".format(data))

        #: Python 3 is annoying
        if hasattr(data, 'encode'):
            data = data.encode()

        self.file.write(data)

    def read(self, size=None):
        return ""

    def disconnect(self):
        log.debug("-- File | closed")
        self.connected = False
        self.protocol.connection_lost()
        if self.file:
            self.file.close()
            self.file = None


