"""Tests for the material pre-feed feature (``Device._prefeed_steps``).

The pre-feed is host-paced: 10 mm pen-up steps, each followed by a delay,
so the average rate matches ``config.prefeed_speed`` in mm/s. Some
firmwares ignore protocol velocity commands.

The model handed to ``_prefeed_steps`` is still in Qt coordinates (y <= 0;
the flip to device space happens later in ``Device.process``), so the feed
extent is the bounding-box height. Moves are relative to ``device.origin``:
after a feed-to-end job the origin sits past the previous cut, and the feed
must never rewind to absolute zero.
"""
import math

import pytest

from atom.api import Bool as ABool
from atom.api import Instance as AInstance
from atom.api import Value
from enaml.qt.QtGui import QPainterPath
from enaml.qt.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qt_app():
    """ QPainterPath and Device instantiation need a Qt application.

    Created lazily rather than at import time: pytest imports every test
    module before running any test, and a bare QGuiApplication created
    during collection would prevent test_app from constructing the
    QApplication that inkcut.app.main() needs.

    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

from inkcut.core.api import Model
from inkcut.core.utils import from_unit
from inkcut.device.plugin import Device, DeviceConfig, DeviceProtocol
from inkcut.device.plugin import TestTransport as InkcutTestTransport
from inkcut.job.models import JobInfo


STEP_PX = from_unit(10, "mm")
HEIGHT = 250.0
N_OUT = int(math.ceil(HEIGHT / STEP_PX))


class RecordingProtocol(object):
    """Record velocity calls so their ordering can be verified."""

    def __init__(self):
        self.calls = []

    def set_velocity(self, velocity):
        self.calls.append(("V", velocity))


class NoVelocityProtocol(object):
    """Represent a protocol without velocity support, such as bare HPGL."""


def flatten(device, steps, protocol):
    """Execute fake steps and return their operations and delays."""
    operations = []
    for function, args, delay in steps:
        if getattr(function, "__self__", None) is device:
            operations.append((("move", tuple(args[0])), delay))
        else:
            function(*args)
            operations.append((protocol.calls[-1], delay))
    return operations


def make_model(width=100, height=250):
    """Create a negative-y model in the form produced by ``Device.init``."""
    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(width, -height)
    return path


def make_device(origin=None):
    """Create the minimal Device state needed by the pre-feed helper."""
    device = Device.__new__(Device)
    if origin is not None:
        device.origin = origin
    return device


def move_operations(operations):
    """Select recorded move operations and their delays."""
    return [(operation, delay) for operation, delay in operations
            if operation[0] == "move"]


def test_prefeed_defaults_build_host_paced_round_trip():
    """Default pre-feed builds a pen-up round trip paced at 100 mm/s."""
    device = make_device()
    config = DeviceConfig(prefeed=True)
    protocol = RecordingProtocol()
    steps = device._prefeed_steps(make_model(), config, protocol)
    operations = flatten(device, steps, protocol)

    assert not [operation for operation, delay in operations
                if operation[0] == "V"]

    moves = move_operations(operations)
    y_positions = [operation[1][1] for operation, delay in moves]
    assert len(y_positions) > 0 and max(y_positions) == HEIGHT

    outward_count = len([
        1 for index, y_position in enumerate(y_positions)
        if index == 0 or y_position > y_positions[index - 1]
    ])
    assert len(moves) == 2 * N_OUT and outward_count == N_OUT
    assert (
        y_positions[:N_OUT] == sorted(y_positions[:N_OUT])
        and y_positions[N_OUT - 1] == HEIGHT
        and y_positions[N_OUT:] == sorted(y_positions[N_OUT:], reverse=True)
        and y_positions[-1] == 0.0
    )
    assert all(operation[1][2] == 0 for operation, delay in moves)

    full_delays = [
        delay
        for (operation, delay), y_start, y_end in zip(
            moves, [0.0] + y_positions[:-1], y_positions
        )
        if abs(abs(y_end - y_start) - STEP_PX) < 1e-6
    ]
    assert full_delays and all(
        abs(delay - 100.0) < 1e-6 for delay in full_delays
    )
    assert all(
        abs(
            delay
            - abs(y_end - y_start) / from_unit(100, "mm") * 1000
        ) < 1e-6
        for (operation, delay), y_start, y_end in zip(
            moves, [0.0] + y_positions[:-1], y_positions
        )
    )


def test_prefeed_uses_device_origin():
    """Pre-feed stays relative to origin so completed jobs never cause rewind."""
    device = make_device(origin=[7.0, 120.0, 0])
    config = DeviceConfig(prefeed=True)
    protocol = RecordingProtocol()
    operations = flatten(
        device, device._prefeed_steps(make_model(), config, protocol), protocol
    )
    moves = move_operations(operations)
    y_positions = [operation[1][1] for operation, delay in moves]
    x_positions = [operation[1][0] for operation, delay in moves]

    assert (
        min(y_positions) == 120.0
        and max(y_positions) == 120.0 + HEIGHT
        and y_positions[-1] == 120.0
    )
    assert all(y_position >= 120.0 for y_position in y_positions)
    assert all(x_position == 7.0 for x_position in x_positions)


def test_prefeed_restores_cut_velocity():
    """Explicit cut velocity is restored after the temporary pre-feed pace."""
    device = make_device()
    config = DeviceConfig(prefeed=True, cut_velocity=8)
    protocol = RecordingProtocol()
    operations = flatten(
        device, device._prefeed_steps(make_model(), config, protocol), protocol
    )

    assert operations[0][0] == ("V", 10) and operations[-1][0] == ("V", 8)
    assert operations[0][1] == 0.0 and operations[-1][1] == 0.0


def test_speed_enabled_emits_only_leading_prefeed_velocity():
    """Job speed mode leaves restoration to the job loop to avoid duplicate setup."""
    device = make_device()
    config = DeviceConfig(prefeed=True, speed_enabled=True)
    protocol = RecordingProtocol()
    operations = flatten(
        device, device._prefeed_steps(make_model(), config, protocol), protocol
    )

    assert operations[0][0] == ("V", 10) and operations[-1][0][0] == "move"


def test_prefeed_disabled_returns_no_steps():
    """Disabling pre-feed prevents all material-feed setup steps."""
    device = make_device()
    config = DeviceConfig(prefeed=False)
    protocol = RecordingProtocol()

    steps = device._prefeed_steps(make_model(), config, protocol)

    assert steps == []


def test_disabled_prefeed_still_sets_cut_velocity():
    """Cut velocity remains honored when material pre-feed is disabled."""
    device = make_device()
    config = DeviceConfig(prefeed=False, cut_velocity=12)
    protocol = RecordingProtocol()
    operations = flatten(
        device, device._prefeed_steps(make_model(), config, protocol), protocol
    )

    assert [operation for operation, delay in operations] == [("V", 12)]


def test_protocol_without_velocity_still_builds_moves():
    """Protocols lacking velocity support still receive every stepped move."""
    device = make_device()
    config = DeviceConfig(prefeed=True, cut_velocity=8)
    protocol = NoVelocityProtocol()

    steps = device._prefeed_steps(make_model(), config, protocol)

    assert (
        len(steps) == 2 * N_OUT
        and all(
            getattr(function, "__self__", None) is device
            for function, args, delay in steps
        )
    )


def test_slower_prefeed_doubles_full_step_delay():
    """A 50 mm/s pre-feed doubles full-step delay and emits its protocol pace."""
    device = make_device()
    config = DeviceConfig(prefeed=True, prefeed_speed=50.0, cut_velocity=8)
    protocol = RecordingProtocol()
    operations = flatten(
        device, device._prefeed_steps(make_model(), config, protocol), protocol
    )
    full_delays = [
        delay for operation, delay in operations
        if operation[0] == "move" and abs(delay - 200.0) < 1e-6
    ]

    assert operations[0][0] == ("V", 5) and len(full_delays) > 0


def test_zero_height_model_only_sets_cut_velocity():
    """A zero-height model avoids feed moves while preserving cut velocity."""
    flat_model = QPainterPath()
    flat_model.moveTo(0, 0)
    flat_model.lineTo(50, 0)
    device = make_device()
    config = DeviceConfig(prefeed=True, cut_velocity=6)
    protocol = RecordingProtocol()

    operations = flatten(
        device, device._prefeed_steps(flat_model, config, protocol), protocol
    )

    assert [operation for operation, delay in operations] == [("V", 6)]


def test_prefeed_config_defaults():
    """New pre-feed fields have safe defaults when older configs are restored."""
    config = DeviceConfig()

    assert (
        config.prefeed is False
        and abs(config.prefeed_speed - 100.0) < 1e-9
        and config.cut_velocity == 0
    )


class SetupRecordingProtocol(DeviceProtocol):
    """Record job setup calls without communicating with cutter hardware."""

    calls = Value(factory=list)

    def connection_made(self):
        self.calls.append(("connected",))

    def move(self, x, y, z, absolute=True):
        self.calls.append(("move", x, y, z))

    def set_force(self, force):
        self.calls.append(("F", force))

    def set_velocity(self, velocity):
        self.calls.append(("V", velocity))

    def finish(self):
        self.calls.append(("finish",))


class DeadTransport(InkcutTestTransport):
    """Simulate a cutter connection that drops before the job starts."""

    def connect(self):
        self.protocol.transport = self
        self.protocol.connection_made()
        # ``connected`` deliberately remains false.


class FakeJob(Model):
    """Provide only the job state needed by ``Device.submit``."""

    info = AInstance(JobInfo, ())
    feed_to_end = ABool()


class PrefeedDevice(Device):
    """Return a canned model without parsing a real job."""

    test_model = Value()

    def init(self, job):
        return self.test_model


def run_submit(transport, cancelled):
    """Submit a synchronous fake job and capture its result and protocol calls."""
    protocol = transport.protocol
    config = DeviceConfig(
        prefeed=True,
        force_enabled=True,
        force=40,
        speed_enabled=True,
        speed=8,
        custom_rate=0.0,
    )
    device = PrefeedDevice(
        connection=transport, config=config, test_model=make_model()
    )
    job = FakeJob()
    job.info.auto_approve = True
    job.info.cancelled = cancelled
    result = {}
    deferred = device.submit(job)
    deferred.addCallbacks(
        lambda value: result.setdefault("ok", value),
        lambda failure: result.setdefault("failure", failure),
    )
    return device, job, protocol.calls, result


def test_cancelled_prefeed_short_circuits_job_setup():
    """Cancellation before pre-feed prevents later setup and working status."""
    device, job, calls, result = run_submit(
        InkcutTestTransport(protocol=SetupRecordingProtocol()), cancelled=True
    )

    assert "ok" in result and "failure" not in result
    assert not [call for call in calls if call[0] in ("F", "V")]
    assert not [call for call in calls if call[0] == "move"]
    assert device.status == "Job cancelled" and job.info.status == "cancelled"


def test_dead_connection_short_circuits_job_setup():
    """A dead connection prevents setup, finish, and misleading working status."""
    device, job, calls, result = run_submit(
        DeadTransport(protocol=SetupRecordingProtocol()), cancelled=False
    )

    assert "ok" in result and "failure" not in result
    assert not [call for call in calls if call[0] in ("F", "V")]
    assert ("finish",) not in calls
    assert device.status == "connection error" and job.info.status == "error"
