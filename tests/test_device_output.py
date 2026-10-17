"""The cutter runs the oriented document path, and the preview draws it.

No cutter and no workbench. Run with QT_QPA_PLATFORM=offscreen.
"""
import pytest
from enaml.qt.QtGui import QPainterPath, QTransform

from inkcut.core.svg import QtSvgDoc
from inkcut.core.utils import from_unit
from inkcut.device.plugin import Device, DeviceConfig, orient_bed
from inkcut.job.models import Job, Material, move_path_of
from inkcut.job.plugin import JobPlugin


SVG = "tests/data/rect.svg"

# swap, scale, padding, artwork screen (x, y, w, h), feed in the path, bed screen
CASES = [
    (False, (1, 1), [0, 0, 0, 0], (0, 0, 200, 50), (0, -80), (0, 0, 1000, 400)),
    (True, (1, 1), [0, 0, 0, 0], (0, 0, 50, 200), (80, 0), (0, 0, 400, 1000)),
    (True, (1, 1), [10, 0, 0, 20], (20, 0, 50, 200), (100, 0), (0, 0, 400, 1000)),
    (True, (2, 1), [10, 0, 0, 20], (20, 0, 50, 400), (100, 0), (0, 0, 400, 2000)),
    (False, (-1, 1), [0, 0, 0, 0], (0, 0, 200, 50), (200, -80), (0, 0, 1000, 400)),
    (True, (-1, 1), [0, 0, 0, 0], (0, 0, 50, 200), (80, 0), (0, 0, 400, 1000)),
    (False, (1, 1), [10, 0, 0, 20], (10, 20, 200, 50), (0, -100), (0, 0, 1000, 400)),
]


def make_job(padding):
    job = Job(material=Material(size=[1000, 400], padding=list(padding)))
    job.path = QtSvgDoc(SVG)
    job._blocked = True
    path = QPainterPath()
    path.addRect(0, 0, 200, 50)
    job.optimized_path = path
    job.feed_to_end = True
    job.feed_after = 30
    job.copies = 1
    job._desired_copies = 1
    job.model = job.create()
    return job


def make_device(swap_xy=False, scale=(1, 1), origin=(0, 0),
                mirror_x=False, mirror_y=False):
    config = DeviceConfig(
        swap_xy=swap_xy,
        scale=[scale[0], scale[1]],
        mirror_x=mirror_x,
        mirror_y=mirror_y,
    )
    return Device(config=config, origin=[origin[0], origin[1], 0])


def feed_point(path):
    element = path.elementAt(path.elementCount() - 1)
    assert element.isMoveTo()
    return (element.x, element.y)


def artwork(path):
    # The feed is a final moveTo and is not part of the artwork box.
    count = path.elementCount()
    trimmed = QPainterPath()
    for i in range(count - 1):
        element = path.elementAt(i)
        if element.isMoveTo():
            trimmed.moveTo(element.x, element.y)
        elif element.isLineTo():
            trimmed.lineTo(element.x, element.y)
        else:
            raise AssertionError("unexpected element %s" % element.type)
    return trimmed


def screen_box(path):
    rect = QTransform.fromScale(1, -1).map(path).boundingRect()
    return (rect.left(), rect.top(), rect.width(), rect.height())


def assert_inside(inner, outer):
    ix, iy, iw, ih = inner
    ox, oy, ow, oh = outer
    assert ix >= ox - 1e-6
    assert iy >= oy - 1e-6
    assert ix + iw <= ox + ow + 1e-6
    assert iy + ih <= oy + oh + 1e-6


@pytest.mark.parametrize(
    "swap_xy, scale, padding, art, feed, bed",
    CASES,
    ids=[
        "swap-off",
        "swap-on",
        "swap-on-padding",
        "swap-on-scale-2-1",
        "mirror-x-swap-off",
        "mirror-x-swap-on",
        "swap-off-padding",
    ],
)
def test_oriented_path_matches_the_bed(swap_xy, scale, padding, art, feed, bed):
    job = make_job(padding)
    device = make_device(swap_xy=swap_xy, scale=scale)
    path = device.output_path(job)
    assert feed_point(path) == pytest.approx(feed)
    art_box = screen_box(artwork(path))
    assert art_box == pytest.approx(art)

    outline = orient_bed(job.material.path, swap_xy, device.output_scale())
    bounds = outline.boundingRect()
    assert bounds.left() == pytest.approx(0)
    assert bounds.bottom() == pytest.approx(0)
    bed_box = screen_box(outline)
    assert bed_box == pytest.approx(bed)
    assert_inside(art_box, bed_box)
    assert job.copies == 1


def device_end(path):
    x, y = feed_point(path)
    return (x, -y)


def test_swap_off_device_end():
    path = make_device(swap_xy=False).output_path(make_job([0, 0, 0, 0]))
    assert device_end(path) == pytest.approx((0, 80))


def test_swap_on_device_end():
    path = make_device(swap_xy=True).output_path(make_job([0, 0, 0, 0]))
    assert device_end(path) == pytest.approx((80, 0))
    assert screen_box(artwork(path)) == pytest.approx((0, 0, 50, 200))


def return_job(padding):
    job = make_job(padding)
    job.feed_to_end = False
    job.model = job.create()
    return job


def test_swap_off_return_stays_at_the_origin():
    path = make_device(swap_xy=False).output_path(return_job([0, 0, 0, 0]))
    assert device_end(path) == pytest.approx((0, 0))
    assert screen_box(artwork(path)) == pytest.approx((0, 0, 200, 50))


def test_swap_on_return_ends_at_bottom_left():
    path = make_device(swap_xy=True).output_path(return_job([0, 0, 0, 0]))
    assert device_end(path) == pytest.approx((0, 0))
    assert screen_box(artwork(path)) == pytest.approx((0, 0, 50, 200))
    moves = move_path_of(path)
    end = moves.elementAt(moves.elementCount() - 1)
    assert (end.x, end.y) == pytest.approx((0, 0))


def test_swap_on_padding_keeps_the_inset():
    path = make_device(swap_xy=True).output_path(make_job([10, 0, 0, 20]))
    assert screen_box(artwork(path)) == pytest.approx((20, 0, 50, 200))
    assert device_end(path) == pytest.approx((100, 0))


def test_output_path_does_not_mutate_job_model():
    job = make_job([0, 0, 0, 0])
    make_device(swap_xy=True).output_path(job)
    assert feed_point(job.model) == pytest.approx((0, -80))


@pytest.fixture
def quiet_job_str(monkeypatch):
    # init logs the job. Formatting it reads document, which needs a workbench.
    monkeypatch.setattr(Job, "__str__", lambda self: "job")


def test_origin_translates_the_swapped_feed(quiet_job_str):
    job = make_job([0, 0, 0, 0])
    device = make_device(swap_xy=True, origin=(5, 7))
    path = device.init(job)
    assert feed_point(path) == pytest.approx((85, -7))
    units = device.config.speed_units.split("/")[0]
    assert job.info.speed == from_unit(device.config.speed, units)


def test_init_matches_output_path(quiet_job_str):
    job = make_job([0, 0, 0, 0])
    device = make_device(swap_xy=True)
    via_init = device.init(job)
    via_output = device.output_path(job)
    assert feed_point(via_init) == pytest.approx(feed_point(via_output))
    assert screen_box(artwork(via_init)) == pytest.approx(
        screen_box(artwork(via_output))
    )


def test_mirror_is_folded_into_init_scale():
    mirrored = make_device(scale=(2, 3), mirror_x=True, mirror_y=True)
    scale = mirrored.output_scale()
    assert scale[0] == pytest.approx(-2)
    assert scale[1] == pytest.approx(-3)
    assert mirrored.config.scale[0] == pytest.approx(2)
    assert mirrored.config.scale[1] == pytest.approx(3)

    job = make_job([0, 0, 0, 0])
    folded = make_device(swap_xy=True, mirror_x=True)
    explicit = make_device(swap_xy=True, scale=(-1, 1))
    folded_path = folded.output_path(job)
    explicit_path = explicit.output_path(make_job([0, 0, 0, 0]))
    assert feed_point(folded_path) == pytest.approx(feed_point(explicit_path))
    assert screen_box(artwork(folded_path)) == pytest.approx(
        screen_box(artwork(explicit_path))
    )


def test_config_rotation_is_not_on_the_output_path():
    plain = make_device(swap_xy=True).output_path(make_job([0, 0, 0, 0]))
    turned_device = make_device(swap_xy=True)
    turned_device.config.rotation = 90
    turned = turned_device.output_path(make_job([0, 0, 0, 0]))
    assert feed_point(plain) == pytest.approx(feed_point(turned))
    assert screen_box(artwork(plain)) == pytest.approx(screen_box(artwork(turned)))
    assert screen_box(artwork(turned)) == pytest.approx((0, 0, 50, 200))


def test_pen_up_path_draws_the_feed():
    path = make_device(swap_xy=True).output_path(make_job([0, 0, 0, 0]))
    moves = move_path_of(path)
    end = moves.elementAt(moves.elementCount() - 1)
    assert end.isLineTo()
    assert (end.x, end.y) == pytest.approx((80, 0))


def test_preview_refresh_does_not_grow_copies(quiet_job_str):
    job = make_job([0, 0, 0, 0])
    job.auto_copies = True
    sentinel = QPainterPath()
    sentinel.addRect(1, 2, 3, 4)
    job.model = sentinel
    device = make_device()
    assert device.preview_output_path(job) is not None
    assert job.copies == 1
    assert job._desired_copies == 1
    assert job.model is sentinel

    cut = make_job([0, 0, 0, 0])
    cut.auto_copies = True
    cut._blocked = False
    device.init(cut)
    assert cut.copies == 1

    growing = make_job([0, 0, 0, 0])
    growing.auto_copies = True
    growing._blocked = False
    growing.update_document()
    assert growing.copies > 1


def test_job_plugin_imports():
    assert callable(JobPlugin._refresh_preview)
