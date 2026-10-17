"""Plotter units emitted by DM/PL and HP-GL.

No window, serial port, or application boot.
"""
import enaml
import pytest

from inkcut.device import plugin as device_plugin
from inkcut.device.extensions import DeviceDriver, DeviceProtocol
from inkcut.device.protocols.dmpl import DMPLConfig, DMPLProtocol
from inkcut.device.protocols.hpgl import HPGLConfig, HPGLProtocol
from inkcut.device.protocols.units import (
    ADDRESSING_0_001_INCH,
    ADDRESSING_0_005_INCH,
    ADDRESSING_0_025_MM,
    ADDRESSING_0_1_MM,
    ADDRESSING_LEGACY,
    ADDRESSING_ORDER,
    units_per_inch,
)

with enaml.imports():
    from inkcut.device.drivers.manifest import DriversManifest
    from inkcut.device.protocols.manifest import dmpl_factory, hpgl_factory


ONE_INCH = 90

ADDRESSING_UNITS = (
    (ADDRESSING_0_001_INCH, 1000),
    (ADDRESSING_0_025_MM, 1016),
    (ADDRESSING_0_1_MM, 254),
    (ADDRESSING_0_005_INCH, 200),
    (ADDRESSING_LEGACY, 1021),
)


class ProtocolConfigDriver:
    def __init__(self, protocol_config):
        self._protocol_config = protocol_config

    def get_protocol_config(self, protocol_id):
        return self._protocol_config.get(protocol_id, {})


def connect(protocol):
    transport = device_plugin.TestTransport(protocol=protocol)
    transport.connect()
    return transport


def take(transport):
    data = transport.buffer.getvalue()
    transport.buffer.seek(0)
    transport.buffer.truncate()
    return data


def dmpl_down(mode, x, y):
    if mode in (1, 2, 3, 4):
        return " D{},{} ".format(x, y).encode()
    return "PD{},{};".format(x, y).encode()


def test_units_per_inch_map():
    assert list(ADDRESSING_ORDER) == [
        "0.001 inch",
        "0.025 mm",
        "0.1 mm",
        "0.005 inch",
        "1021 per inch",
    ]
    for name, units in ADDRESSING_UNITS:
        assert units_per_inch(name) == units


def test_addressing_defaults_to_legacy_and_is_not_a_saved_scale():
    assert ADDRESSING_ORDER[0] != ADDRESSING_LEGACY
    assert tuple(DMPLConfig.addressing.items) == ADDRESSING_ORDER
    assert tuple(HPGLConfig.addressing.items) == ADDRESSING_ORDER
    assert DMPLConfig().addressing == ADDRESSING_LEGACY
    assert HPGLConfig().addressing == ADDRESSING_LEGACY
    for config in (DMPLConfig(), HPGLConfig()):
        state = config.__getstate__()
        assert state["addressing"] == ADDRESSING_LEGACY
        assert "scale" not in state
        assert not any(isinstance(value, float) for value in state.values())


def test_dmpl_mode1_commands_thousandth_inch():
    protocol = DMPLProtocol(config=DMPLConfig(
        mode=1, addressing=ADDRESSING_0_1_MM,
    ))
    transport = connect(protocol)
    connected = take(transport)
    assert connected == b";:HAEC1"
    assert b";:HAEC1" in connected
    protocol.move(ONE_INCH, 0, 1)
    assert take(transport) == b" D1000,0 "
    protocol.move(0, ONE_INCH, 1)
    assert take(transport) == b" D0,1000 "
    # int() truncates; round(5 * 1000 / 90) would be 56.
    protocol.move(5, 0, 1)
    assert take(transport) == b" D55,0 "
    protocol.config.addressing = ADDRESSING_LEGACY
    assert take(transport) == b""
    protocol.move(ONE_INCH, 0, 1)
    assert take(transport) == b" D1000,0 "


def test_dmpl_mode2_commands_025_mm():
    protocol = DMPLProtocol(config=DMPLConfig(
        mode=2, addressing=ADDRESSING_0_001_INCH,
    ))
    transport = connect(protocol)
    connected = take(transport)
    assert connected == b" ;:ECN A L0 "
    assert b"ECN" in connected
    protocol.move(ONE_INCH, 0, 1)
    assert take(transport) == b" D1016,0 "
    protocol.move(0, ONE_INCH, 1)
    assert take(transport) == b" D0,1016 "
    protocol.config.addressing = ADDRESSING_0_1_MM
    assert take(transport) == b""
    protocol.move(ONE_INCH, 0, 1)
    assert take(transport) == b" D1016,0 "


@pytest.mark.parametrize("mode,connect_bytes", (
    (3, b" ;:H A L0 "),
    (4, b" ;:H A L0 "),
    (6, b"IN;PA;"),
))
@pytest.mark.parametrize("addressing,units", ADDRESSING_UNITS)
def test_dmpl_addressing_modes_scale_without_ec(mode, connect_bytes, addressing, units):
    config = DMPLConfig()
    config.__setstate__({"mode": mode})
    if addressing != ADDRESSING_LEGACY:
        config.addressing = addressing
    assert config.addressing == addressing
    protocol = DMPLProtocol(config=config)
    transport = connect(protocol)
    connected = take(transport)
    assert connected == connect_bytes
    assert b"EC" not in connected
    protocol.move(ONE_INCH, 0, 1)
    assert take(transport) == dmpl_down(mode, units, 0)
    protocol.move(0, ONE_INCH, 1)
    assert take(transport) == dmpl_down(mode, 0, units)


@pytest.mark.parametrize("mode,connect_bytes", (
    (3, b" ;:H A L0 "),
    (4, b" ;:H A L0 "),
    (6, b"IN;PA;"),
))
def test_dmpl_addressing_change_does_not_write_ec(mode, connect_bytes):
    protocol = DMPLProtocol(config=DMPLConfig(mode=mode))
    transport = connect(protocol)
    assert take(transport) == connect_bytes
    protocol.config.addressing = ADDRESSING_0_001_INCH
    assert take(transport) == b""
    protocol.move(ONE_INCH, 0, 1)
    moved = take(transport)
    assert b"EC" not in moved
    assert moved == dmpl_down(mode, 1000, 0)
    # int() truncates on the addressing path; round(2 * 1021 / 90) is 23.
    protocol.config.addressing = ADDRESSING_LEGACY
    protocol.move(2, 0, 1)
    assert take(transport) == dmpl_down(mode, 22, 0)


@pytest.mark.parametrize("saved,units", (
    ({}, 1021),
    ({"pad": False, "separate_z_moves": False}, 1021),
    ({"addressing": ADDRESSING_0_001_INCH}, 1000),
    ({"addressing": ADDRESSING_0_025_MM}, 1016),
    ({"addressing": ADDRESSING_0_1_MM}, 254),
    ({"addressing": ADDRESSING_0_005_INCH}, 200),
    ({"addressing": ADDRESSING_LEGACY}, 1021),
))
def test_hpgl_addressing_units(saved, units):
    config = HPGLConfig()
    config.__setstate__(dict(saved))
    if "addressing" not in saved:
        assert config.addressing == ADDRESSING_LEGACY
    protocol = HPGLProtocol(config=config)
    transport = connect(protocol)
    assert take(transport) == b"IN;"
    protocol.move(ONE_INCH, 0, 1)
    assert take(transport) == "PD{},0;".format(units).encode()
    protocol.move(0, ONE_INCH, 1)
    assert take(transport) == "PD0,{};".format(units).encode()


def test_hpgl_legacy_truncates():
    protocol = HPGLProtocol()
    transport = connect(protocol)
    take(transport)
    protocol.move(2, 0, 1)
    assert take(transport) == b"PD22,0;"


def test_hpgl_factory_uses_protocol_config():
    driver = ProtocolConfigDriver({
        "hpgl": {"addressing": ADDRESSING_0_025_MM},
    })
    protocol = hpgl_factory(driver, None)
    transport = connect(protocol)
    take(transport)
    protocol.move(ONE_INCH, 0, 1)
    assert take(transport) == b"PD1016,0;"


@pytest.mark.parametrize("protocol_config", (
    {},
    {"hpgl": {}},
))
def test_hpgl_factory_empty_config_is_legacy(protocol_config):
    protocol = hpgl_factory(ProtocolConfigDriver(protocol_config), None)
    assert protocol.config.addressing == ADDRESSING_LEGACY
    transport = connect(protocol)
    take(transport)
    protocol.move(ONE_INCH, 0, 1)
    assert take(transport) == b"PD1021,0;"


def summa_d760():
    for extension in DriversManifest().extensions:
        for driver in extension.get_children(DeviceDriver):
            if driver.manufacturer == "Summa" and driver.model == "D760":
                return driver
    raise AssertionError("Summa D760 was not declared")


class ProtocolRegistry:
    """Stand-in for DevicePlugin. Holds the shared protocol registry."""

    def __init__(self, protocols):
        self.protocols = protocols
        self.transports = []


def registration_order():
    """HP-GL is registered before DM/PL, as in the protocol manifest."""
    return [
        DeviceProtocol(id="gpgl", name="GPGL"),
        DeviceProtocol(id="hpgl", name="HPGL"),
        DeviceProtocol(id="dmpl", name="DMPL"),
    ]


def test_d760_factories_use_declared_units():
    driver = summa_d760()
    assert driver.width == "740mm"
    assert driver.length == ""
    assert driver.initial_protocol == "dmpl"
    assert list(driver.protocols) == ["hpgl", "dmpl"]
    assert "scale" not in driver.default_config
    device_config = driver.get_device_config()
    assert "scale" not in device_config
    assert "protocol" not in device_config
    assert list(device_plugin.DeviceConfig(**device_config).scale) == [1, 1]

    dmpl = dmpl_factory(driver, None)
    transport = connect(dmpl)
    assert take(transport) == b";:HAEC1"
    dmpl.move(ONE_INCH, 0, 1)
    assert take(transport) == b" D1000,0 "
    dmpl.move(0, ONE_INCH, 1)
    assert take(transport) == b" D0,1000 "

    hpgl = hpgl_factory(driver, None)
    transport = connect(hpgl)
    take(transport)
    hpgl.move(ONE_INCH, 0, 1)
    assert take(transport) == b"PD1016,0;"
    hpgl.move(0, ONE_INCH, 1)
    assert take(transport) == b"PD0,1016;"


def test_initial_protocol_is_local_and_does_not_reorder_the_registry():
    registered = registration_order()
    registry = ProtocolRegistry(registered)
    order_before = [protocol.id for protocol in registry.protocols]

    device = device_plugin.DevicePlugin.get_device_from_driver(
        registry, summa_d760(),
    )
    assert [protocol.id for protocol in device.protocols] == ["dmpl", "hpgl"]
    assert list(device.config.scale) == [1, 1]
    assert [protocol.id for protocol in registry.protocols] == order_before
    assert registry.protocols is registered

    plain = DeviceDriver(
        manufacturer="Example",
        model="HpglDmpl",
        width="10cm",
        protocols=["dmpl", "hpgl"],
    )
    assert plain.initial_protocol == ""
    device = device_plugin.DevicePlugin.get_device_from_driver(registry, plain)
    assert [protocol.id for protocol in device.protocols] == ["hpgl", "dmpl"]
    assert list(device.config.scale) == [1, 1]
    assert [protocol.id for protocol in registry.protocols] == order_before
