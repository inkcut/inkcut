# -*- coding: utf-8 -*-
"""
Copyright (c) 2019, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on June 7, 2019

@author: jrm
"""
import re
import sys
import traceback
import subprocess
from glob import glob
from atom.api import Atom, List, Unicode, Instance
from inkcut.core.api import Plugin, log

from inkcut.device.transports.raw.plugin import (
    RawFdTransport, RawFdProtocol, RawFdConfig
)


class ParallelPortDescriptor(Atom):
    name = Unicode()
    device = Unicode()

    def __str__(self):
        return "{} ({})".format(self.name, self.device)


def find_dev_name(dev):
    """ Use udevadm to lookup info on a device

    Parameters
    ----------
    dev: String
        The device path to lookup, eg /dev/usb/lp1

    Returns
    -------
    name: String
        The device name

    """
    try:
        cmd = 'udevadm info -a %s' % dev
        manufacturer = ""
        product = ""

        output = subprocess.check_output(cmd.split())
        if sys.version_info.major > 2:
            output = output.decode()
        for line in output.split('\n'):
            log.debug(line)
            m = re.search(r'ATTRS{(.+)}=="(.+)"', line)
            if m:
                k, v = m.groups()
                if k == 'manufacturer':
                    manufacturer = v.strip()
                elif k == 'product':
                    product = v.strip()
            if manufacturer and product:
                return '{} {}'.format(manufacturer, product)
        log.warning('Could not lookup device info for %s' % dev)
    except Exception as e:
        tb = traceback.format_exc()
        log.warning('Could not lookup device info for %s  %s' % (dev, tb))
    return 'usb%s' % dev.split('/')[-1]


def find_ports():
    """ Lookup ports from known locations on the system

    Returns
    -------
    ports: List[ParallelPortDescriptor]
        The ports found on the system

    """
    ports = []
    if 'win32' in sys.platform:
        pass  # TODO
    elif 'darwin' in sys.platform:
        pass  # TODO
    else:
        for p in glob('/dev/lp*'):
            # TODO: Get friendly device name
            name = p.split('/')[-1]
            ports.append(ParallelPortDescriptor(device=p, name=name))

        for p in glob('/dev/parport*'):
            # TODO: Get friendly device name
            name = p.split('/')[-1]
            ports.append(ParallelPortDescriptor(device=p, name=name))

        for p in glob('/dev/usb/lp*'):
            name = find_dev_name(p)
            ports.append(ParallelPortDescriptor(device=p, name=name))

    return ports


class ParallelConfig(RawFdConfig):
    #: Available serial ports
    ports = List(ParallelPortDescriptor)

    # -------------------------------------------------------------------------
    # Defaults
    # -------------------------------------------------------------------------
    def _default_ports(self):
        return find_ports()

    def _default_device_path(self):
        if self.ports:
            return self.ports[0].device
        return ""

    def refresh(self):
        self.ports = self._default_ports()


class ParallelTransport(RawFdTransport):
    """ This is just a wrapper for the RawFdTransport

    """
    #: Default config
    config = Instance(ParallelConfig, ()).tag(config=True)


class ParallelPlugin(Plugin):
    """ Plugin for handling parallel port communication

    """
