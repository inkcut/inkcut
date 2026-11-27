import asyncio
import pytest
from io import BytesIO
from atom.api import Bool, Bytes, List
from inkcut.device.plugin import DebugTransport
from inkcut.device.protocols.hpgl import HPGLProtocol
from inkcut.device.protocols.dmpl import DMPLProtocol
from inkcut.device.protocols.gpgl import GPGLProtocol, SENTINEL, STATE


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


async def test_gpgl_append_etx():
    protocol = GPGLProtocol()
    protocol.config.append_etx = True
    transport = DebugTransport(protocol=protocol)
    await transport.connect()
    expect_written(transport, b"\x03\x03H\x03")
    await protocol.move(1, 4, 0)
    expect_written(transport, b"\x03M1,4\x03")


class FakeCameo(DebugTransport):
    """ Answers state queries with `state`, and each batch's query too if
    `answer` is set. Records the other writes. """
    state = Bytes(b'1')
    answer = Bool(True)
    writes = List()

    async def write(self, data):
        loop = asyncio.get_running_loop()
        if data == STATE:
            loop.call_soon(self.protocol.data_received, self.state + b'\x03')
            return
        self.writes.append(data)
        if self.answer and data.endswith(SENTINEL):
            loop.call_soon(self.protocol.data_received, b'CAMEO 4\x03')


async def gpgl_flow(**kwargs):
    protocol = GPGLProtocol(lost_after=0.1, **kwargs)
    protocol.config.append_etx = True
    protocol.config.flow_control = True
    transport = FakeCameo(protocol=protocol)
    await transport.connect()
    transport.writes = []
    return protocol, transport


async def test_gpgl_flow_batches():
    protocol, transport = await gpgl_flow()
    await protocol.start_job()
    for i in range(40):
        await protocol.move(i, i, 1)
    await protocol.finish()
    sent = ''.join(transport.writes).replace(SENTINEL, '')
    assert sent == ''.join('\x03D%i,%i\x03' % (i, i) for i in range(40))
    assert len(transport.writes) > 1
    for w in transport.writes:
        assert w.endswith(SENTINEL)
        assert len(w) <= protocol.batch_size
    assert protocol._unanswered == 0


async def test_gpgl_flow_off():
    #: Without flow control, or while jogging, each command goes at once
    protocol, transport = await gpgl_flow()
    await protocol.move(1, 2, 0)
    assert transport.writes == ['\x03M1,2\x03']
    protocol.config.flow_control = False
    await protocol.start_job()
    await protocol.move(3, 4, 1)
    await protocol.finish()
    assert transport.writes == ['\x03M1,2\x03', '\x03D3,4\x03']


async def test_gpgl_flow_spooled():
    #: A printer queue never answers, so no flow control there
    protocol, transport = await gpgl_flow()
    transport.always_spools = True
    assert not protocol.controls_flow()


async def test_gpgl_flow_window():
    protocol, transport = await gpgl_flow(window=2)
    transport.answer = False
    await protocol.start_job()

    async def job():
        for i in range(100):
            await protocol.move(i, i, 1)
    task = asyncio.ensure_future(job())
    await asyncio.sleep(0.05)
    assert len(transport.writes) == 2
    protocol.data_received(b'CAMEO 4\x03')
    await asyncio.sleep(0.05)
    assert len(transport.writes) == 3
    task.cancel()


async def test_gpgl_flow_paused():
    #: Nothing is sent while the machine is paused
    protocol, transport = await gpgl_flow()
    await protocol.start_job()
    protocol.status_received(b'3\x03')
    transport.state = b'3'

    async def job():
        for i in range(40):
            await protocol.move(i, i, 1)
        await protocol.finish()
    task = asyncio.ensure_future(job())
    await asyncio.sleep(0.1)
    assert transport.writes == []
    protocol.status_received(b'1\x03')
    transport.state = b'1'
    await asyncio.wait_for(task, 1)
    assert transport.writes


async def test_gpgl_flow_lost():
    #: Batches never answered while the machine sits idle are given up on,
    #: so the job does not hang
    protocol, transport = await gpgl_flow()
    transport.answer = False
    transport.state = b'2'
    await protocol.start_job()
    await protocol.move(1, 2, 1)
    await asyncio.wait_for(protocol.finish(), 2)
    assert protocol._unanswered == 0


class CameoTransport(DebugTransport):
    """ Answers the tool query like a Cameo 4 would, after a write. """
    tools_reply = Bytes(b' 2, 0\x03')

    async def write(self, data):
        await super().write(data)
        if data == "\x1b\x15" and self.tools_reply:
            self.protocol.data_received(self.tools_reply)


async def gpgl_on(transport_cls=DebugTransport, **config):
    protocol = GPGLProtocol(reply_timeout=0.1)
    for k, v in config.items():
        setattr(protocol.config, k, v)
    transport = transport_cls(protocol=protocol)
    await transport.connect()
    expect_written(transport, b"\x03\x03H")
    return protocol, transport


async def test_gpgl_autoblade_off():
    protocol, transport = await gpgl_on(CameoTransport)
    await protocol.start_job()
    expect_written(transport, b"")


async def test_gpgl_autoblade_sets_depth():
    protocol, transport = await gpgl_on(
        CameoTransport, autoblade=True, autoblade_depth=3)
    await protocol.start_job()
    expect_written(transport, b"\x1b\x15\x03J1\x03TF3,1")
    assert protocol.tools == [2, 0]


async def test_gpgl_autoblade_skips_other_tool():
    protocol, transport = await gpgl_on(CameoTransport, autoblade=True)
    transport.tools_reply = b' 1, 0\x03'
    await protocol.start_job()
    expect_written(transport, b"\x1b\x15")
    assert protocol.tools == [1, 0]


async def test_gpgl_autoblade_no_reply():
    #: A machine that does not answer still gets the depth
    protocol, transport = await gpgl_on(autoblade=True, autoblade_depth=5)
    await protocol.start_job()
    expect_written(transport, b"\x1b\x15\x03J1\x03TF5,1")
    assert protocol.tools == []


async def test_gpgl_autoblade_depth_clamped():
    protocol, transport = await gpgl_on(CameoTransport)
    await protocol.set_autoblade_depth(12)
    expect_written(transport, b"\x1b\x15\x03J1\x03TF10,1")


async def test_gpgl_reply_split_across_packets():
    protocol, transport = await gpgl_on()

    async def answer():
        protocol.data_received(b'CAMEO 4 ')
        protocol.data_received(b'PLUS\x03')
    reply = asyncio.ensure_future(protocol.query("FG"))
    await asyncio.sleep(0)
    await answer()
    assert await reply == b'CAMEO 4 PLUS'


async def test_gpgl_force_speed_unconverted():
    #: Without a driver scale, values go out as before (Graphtec drivers)
    protocol, transport = await gpgl_on()
    await protocol.set_force(40)
    expect_written(transport, b"\x03FX40,1")
    await protocol.set_velocity(4)
    expect_written(transport, b"\x03!4")


async def test_gpgl_force_speed_converted():
    protocol, transport = await gpgl_on(
        force_grams_per_unit=7, force_max=33,
        speed_mm_s_per_unit=100, speed_max=30)
    await protocol.set_force(40)  # 40/7 = 5.7
    expect_written(transport, b"\x03FX6,1")
    await protocol.set_velocity(8)  # 203 mm/s
    expect_written(transport, b"\x03!2")
    await protocol.set_force(1000)
    expect_written(transport, b"\x03FX33,1")
    await protocol.set_force(1)
    expect_written(transport, b"\x03FX1,1")
    await protocol.set_velocity(1000)
    expect_written(transport, b"\x03!30")
