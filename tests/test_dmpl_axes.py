"""DMPL axis-transpose tests.

The Anhui-Anyu firmware drives the feed rollers with the first DMPL
coordinate and the carriage with the second, opposite of Inkcut's
device-space convention (y = feed). With ``DMPLConfig.swap_axes`` the
protocol emits (y, x) so feed-to-end, pre-feed, and origin bookkeeping
physically act on the rollers.
"""
import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from inkcut.device.protocols.dmpl import DMPLConfig, DMPLProtocol


class Sink(object):
    """Capture protocol output without requiring a transport or cutter."""

    def __init__(self):
        self.data = ""


def make_protocol(monkeypatch, swap_axes, mode=3):
    """Build a DMPL protocol whose writes are captured in memory."""
    sink = Sink()

    def capture_write(self, data):
        sink.data += data

    # Atom members are fixed, so replace the method on the class.
    monkeypatch.setattr(DMPLProtocol, "write", capture_write)
    protocol = DMPLProtocol()
    protocol.config = DMPLConfig(mode=mode, swap_axes=swap_axes)
    protocol.scale = 1.0
    return protocol, sink


def test_default_axes_pass_through(monkeypatch):
    """Default mode preserves upstream coordinate and pen-state behavior."""
    protocol, sink = make_protocol(monkeypatch, swap_axes=False)

    protocol.move(10, 20, 0)
    assert sink.data == " U10,20 "

    protocol.move(30, 40, 1)
    assert sink.data.endswith(" D30,40 ")


def test_swap_axes_transposes_moves(monkeypatch):
    """Axis swapping routes both pen-up and pen-down feed coordinates correctly."""
    protocol, sink = make_protocol(monkeypatch, swap_axes=True)

    protocol.move(10, 20, 0)
    assert sink.data == " U20,10 "

    protocol.move(30, 40, 1)
    assert sink.data.endswith(" D40,30 ")


def test_swap_axes_transposes_feed_to_end(monkeypatch):
    """Feed-to-end moves media while returning the carriage to zero."""
    protocol, sink = make_protocol(monkeypatch, swap_axes=True)

    protocol.move(0, 23628, 0)

    assert sink.data == " U23628,0 "


def test_swap_axes_transposes_mode_six(monkeypatch):
    """HPGL-style DMPL mode 6 applies the same required axis transpose."""
    protocol, sink = make_protocol(monkeypatch, swap_axes=True, mode=6)

    protocol.move(10, 20, 0)

    assert sink.data == "PU20,10;"


def test_swap_axes_is_persistent_config():
    """The swap option is config-tagged so device settings persist it."""
    assert "config" in (DMPLConfig.swap_axes.metadata or {})
