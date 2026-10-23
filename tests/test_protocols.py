import pytest
from io import BytesIO
from inkcut.device.plugin import DebugTransport
from inkcut.device.protocols.hpgl import HPGLProtocol
from inkcut.device.protocols.dmpl import DMPLProtocol
from inkcut.device.protocols.gpgl import GPGLProtocol


def expect_written(transport: DebugTransport, value: bytes):
    wrote = transport.buffer.getvalue()
    transport.buffer = BytesIO()
    assert wrote == value


async def test_hpgl_protocol():
    protocol = HPGLProtocol(scale=1)
    transport = DebugTransport(protocol=protocol)
    await transport.connect()
    expect_written(transport, b"IN;")

    await protocol.move(3, 2, 1)
    expect_written(transport, b"PD3,2;")
    await protocol.move(1, 4, 0)
    expect_written(transport, b"PU1,4;")

    await protocol.move(1, 2, 0, absolute=False)
    expect_written(transport, b"PR1,2;")

    await protocol.set_force(100)
    expect_written(transport, b"FS100;")

    await protocol.set_velocity(10)
    expect_written(transport, b"VS10;")

    await protocol.set_pen(1)
    expect_written(transport, b"SP1;")

    protocol.config.separate_z_moves = True
    await protocol.move(1, 2, 0)
    expect_written(transport, b"PU;PA1,2;")
    await protocol.move(2, 4, 1)
    expect_written(transport, b"PD;PA2,4;")

    await protocol.finish()
    expect_written(transport, b"IN;")


DMPL_TESTS = {
    1: b";:HAEC1EC1 BP100 V10  D3,2  U1,4 ",
    2: b" ;:ECN A L0 EC1 BP100 V10  D3,2  U1,4 ",
    3: b" ;:H A L0 EC1 BP100 V10  D3,2  U1,4 ",
    4: b" ;:H A L0 EC1 BP100 V10  D3,2  U1,4 ",
    6: b"IN;PA;EC1 BP100 V10 PD3,2;PU1,4;",
}

@pytest.mark.parametrize("mode", DMPL_TESTS.keys())
async def test_dmpl_protocol(mode):
    expected = DMPL_TESTS[mode]
    protocol = DMPLProtocol(scale=1)
    protocol.config.mode = mode
    transport = DebugTransport(protocol=protocol)
    await transport.connect()
    await protocol.set_pen(1)
    await protocol.set_force(100)
    await protocol.set_velocity(10)
    await protocol.move(3, 2, 1)
    await protocol.move(1, 4, 0)
    await protocol.finish()
    assert transport.buffer.getvalue() == expected



async def test_gpgl_protocol():
    protocol = GPGLProtocol()
    transport = DebugTransport(protocol=protocol)
    await transport.connect()
    expect_written(transport, b"H")
    await protocol.set_pen(1)
    expect_written(transport, b"")
    await protocol.set_force(100)
    expect_written(transport, b"FX100,1")
    await protocol.set_velocity(10)
    expect_written(transport, b"!10")
    await protocol.move(3, 2, 1)
    expect_written(transport, b"D3,2")
    await protocol.move(1, 4, 0)
    expect_written(transport, b"M1,4")
    await protocol.finish()
