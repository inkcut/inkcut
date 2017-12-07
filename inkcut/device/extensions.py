# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jan 16, 2015

@author: jrm
"""
from atom.api import (
    Atom, Float, Instance, Unicode, Bool, ForwardInstance,
    List, Int, Callable, Coerced, observe
)
from enaml.core.declarative import Declarative, d_


class DeviceDriver(Declarative):
    """ Provide meta info about this device """
    # ID of the device
    # If none exits one i created from manufacturer.model
    id = d_(Unicode())

    # Name of the device (optional)
    name = d_(Unicode())
    # Model of the device (optional)
    model = d_(Unicode())

    # Manufacturer of the device (optional)
    manufacturer = d_(Unicode())

    # Width of the device (required)
    width = d_(Unicode())

    # Length of the device, if it uses a roll, leave blank
    length = d_(Unicode())

    # Step resolution
    resolution = d_(Unicode())

    # Factory to construct the device,
    # takes a single argument for the protocol
    # implement __setstate__ to load parameters.
    factory = d_(Callable())

    # IDs of the protocols supported by this device
    protocols = d_(List(Unicode()))

    # IDs of the transports supported by this device
    connections = d_(List(Unicode()))


class DeviceProtocol(Declarative):
    # Id of the protocol
    id = d_(Unicode())

    # Name of the protocol (optional)
    name = d_(Unicode())

    # Factory to construct the protocol,
    # takes a single argument for the transport
    factory = d_(Callable())

    # Settings to configure the protocol, must return enaml widgets!
    options = d_(Callable())


class DeviceTransport(Declarative):
    # Id of the protocol
    id = d_(Unicode())

    # Name of the protocol (optional)
    name = d_(Unicode())

    # Factory to construct the protocol,
    # takes a single argument for the transport
    factory = d_(Callable())

    # Settings to configure the protocol, must return enaml widgets!
    view_factory = d_(Callable())
