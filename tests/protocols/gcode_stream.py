"""
Copyright (c) 2024, Karlis Senko

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Oct 20, 2024

@author: karliss
"""

import pytest


from twisted.internet import task, defer


from inkcut.device.plugin import DeviceConfig, Device, TestTransport
from inkcut.device.extensions import DeviceDriver
from inkcut.device.protocols.gcode import GCodeConfig, GCodeProtocol

DATA_PREFIX = "tests/data/filters"


@pytest.fixture(scope="function")
def gcodedevice_fixture():
    config = DeviceConfig()
    config.test_mode = True
    decl = DeviceDriver()
    dev = Device(config=config, declaration=decl)
    gcode_config = GCodeConfig()
    protocol = GCodeProtocol(config=gcode_config)
    dev.connection.protocol = protocol
    return dev


# connect_r_finished = False
def test_ok_streaming(gcodedevice_fixture):
    clock = task.Clock()

    gcode_protocol: GCodeProtocol = gcodedevice_fixture.connection.protocol
    gcode_protocol.config.stream_mode = GCodeConfig.GCODE_STREAM_OK
    gcode_protocol.config.use_builtin = False

    gcode_protocol._reactor = clock

    transport: TestTransport = gcodedevice_fixture.connection

    connect_r = defer.maybeDeferred(gcodedevice_fixture.connect)
    # connect_r.addCallback(finish, 1)
    # clock.callLater(0, connect_r)
    clock.pump([0.01] * 10)
    assert connect_r.called

    # wait for ok to finish
    move1_def = defer.maybeDeferred(gcodedevice_fixture.move, (1, 1, 0))
    assert move1_def.called is False
    clock.pump([0.01] * 10)
    assert move1_def.called is False
    gcode_protocol.data_received(b"ok\n")
    clock.pump([0.01] * 10)
    assert move1_def.called
    assert transport.buffer.getvalue() == b"G00 X1 Y1\n"
    transport.clear_buffer()

    # multipart receive
    move1_def = defer.maybeDeferred(gcodedevice_fixture.move, (1, 2, 0))
    assert move1_def.called is False
    clock.pump([0.01] * 10)
    assert move1_def.called is False
    gcode_protocol.data_received(b"o")
    clock.pump([0.01] * 10)
    assert move1_def.called is False
    gcode_protocol.data_received(b"k\n")
    clock.pump([0.01] * 10)
    assert move1_def.called
    assert transport.buffer.getvalue() == b"G00 X1 Y2\n"
