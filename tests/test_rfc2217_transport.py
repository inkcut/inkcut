"""Regression tests for RFC2217 serial transport."""

import asyncio
from unittest.mock import MagicMock, PropertyMock

import pytest
import serial.rfc2217

from inkcut.device.transports.serialport.serial import (
    connection_for_serial,
)


@pytest.mark.asyncio
async def test_rfc2217_transport_accepts_remote_serial():
    remote = MagicMock(spec=serial.rfc2217.Serial)

    type(remote).write_timeout = PropertyMock(
        side_effect=NotImplementedError(
            "write_timeout is currently not supported"
        )
    )

    remote.port = "rfc2217://127.0.0.1:7000"
    remote.is_open = True
    remote.in_waiting = 0

    transport = None

    try:
        transport, _ = await connection_for_serial(
            asyncio.get_running_loop(),
            asyncio.Protocol,
            remote,
        )

        assert transport is not None

    finally:
        if transport is not None:
            transport.abort()


class RecordingProtocol(asyncio.Protocol):
    def __init__(self):
        self.received = []
        self.connected = asyncio.Event()
        self.closed = asyncio.Event()
        self.error = None

    def connection_made(self, transport):
        self.transport = transport
        self.connected.set()

    def data_received(self, data):
        self.received.append(data)

    def connection_lost(self, exc):
        self.error = exc
        self.closed.set()


def make_remote():
    remote = MagicMock(spec=serial.rfc2217.Serial)
    remote.port = "rfc2217://127.0.0.1:7000"
    remote.is_open = True
    remote.in_waiting = 0
    remote.write.side_effect = lambda data: len(data)

    type(remote).write_timeout = PropertyMock(
        side_effect=NotImplementedError(
            "write_timeout is currently not supported"
        )
    )
    return remote


async def open_remote(remote):
    transport, protocol = await connection_for_serial(
        asyncio.get_running_loop(),
        RecordingProtocol,
        remote,
    )
    await asyncio.wait_for(protocol.connected.wait(), 2)
    return transport, protocol


@pytest.mark.asyncio
async def test_rfc2217_write_order():
    remote = make_remote()
    transport, protocol = await open_remote(remote)

    try:
        transport.write(b"IN;")
        transport.write(b"PU0,0;")
        transport.write(b"PD804,804;")

        transport.close()
        await asyncio.wait_for(protocol.closed.wait(), 2)

        assert [
            call.args[0]
            for call in remote.write.call_args_list
        ] == [
            b"IN;",
            b"PU0,0;",
            b"PD804,804;",
        ]

        remote.close.assert_called_once()
        assert protocol.error is None
    finally:
        if not transport.is_closing():
            transport.abort()


@pytest.mark.asyncio
async def test_rfc2217_receive_data():
    remote = make_remote()

    type(remote).in_waiting = PropertyMock(
        side_effect=[4] + [0] * 1000
    )
    remote.read.return_value = b"TEST"

    transport, protocol = await open_remote(remote)

    try:
        for _ in range(100):
            if protocol.received:
                break
            await asyncio.sleep(0.01)

        assert protocol.received == [b"TEST"]
    finally:
        transport.close()
        await asyncio.wait_for(protocol.closed.wait(), 2)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["exception", "partial"])
async def test_rfc2217_write_failure(failure):
    remote = make_remote()

    if failure == "exception":
        remote.write.side_effect = serial.SerialException(
            "Connection lost"
        )
    else:
        remote.write.side_effect = lambda data: len(data) - 1

    transport, protocol = await open_remote(remote)
    callbacks = []
    transport._wrote_callback = callbacks.append

    transport.write(b"IN;")

    await asyncio.wait_for(protocol.closed.wait(), 2)

    assert isinstance(protocol.error, serial.SerialException)
    assert callbacks == [b""]
    remote.close.assert_called_once()


@pytest.mark.asyncio
async def test_rfc2217_close_connection():
    remote = make_remote()
    transport, protocol = await open_remote(remote)

    transport.close()

    await asyncio.wait_for(protocol.closed.wait(), 2)

    remote.flush.assert_called_once()
    remote.close.assert_called_once()
    assert transport.is_closing()
    assert protocol.error is None
