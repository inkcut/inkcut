"""
Copyright (c) 2026, The Inkcut Team

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.
"""
import importlib.util
from pathlib import Path

import pytest
from lxml import etree
from enaml.qt.QtCore import QPointF

from inkcut.core.svg import QtSvgDoc


SVG = "tests/data/cut-selection.svg"

# Interiors of the four closed shapes. They stay apart under a uniform
# DPI scale, so a hit in one region is not a hit in another.
POINTS = {
    "path-a": (20, 20),
    "path-b": (220, 20),
    "path-c": (20, 220),
    "path-d": (220, 220),
}


def _load_selection():
    path = Path(__file__).resolve().parents[1] / "plugins" / "inkscape" / "selection.py"
    spec = importlib.util.spec_from_file_location("inkcut_inkscape_selection", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


selection = _load_selection()


def regions(doc):
    hit = set()
    for name, (x, y) in POINTS.items():
        if doc.contains(QPointF(x, y)):
            hit.add(name)
    return hit


def test_selected_path_excludes_the_rest():
    doc = QtSvgDoc(SVG, ids=["path-a"])
    assert regions(doc) == {"path-a"}


def test_selected_group_includes_descendants_only():
    doc = QtSvgDoc(SVG, ids=["group-c"])
    assert regions(doc) == {"path-c", "path-d"}


def test_selected_child_excludes_siblings():
    doc = QtSvgDoc(SVG, ids=["path-c"])
    assert regions(doc) == {"path-c"}


def test_unknown_id_does_not_import_the_document():
    with pytest.raises(ValueError) as caught:
        QtSvgDoc(SVG, ids=["does-not-exist"])
    assert "selected" in str(caught.value).lower()


def test_no_ids_imports_the_whole_document():
    doc = QtSvgDoc(SVG, ids=None)
    assert regions(doc) == set(POINTS)


def test_empty_id_list_imports_the_whole_document():
    doc = QtSvgDoc(SVG, ids=[])
    assert regions(doc) == set(POINTS)


def test_partial_id_match_keeps_the_ids_that_exist():
    doc = QtSvgDoc(SVG, ids=["does-not-exist", "path-b"])
    assert regions(doc) == {"path-b"}


def test_conversion_actions_for_a_selection_do_not_select_all():
    actions = selection.conversion_actions(["a", "b", "c"])
    assert actions == (
        "select-by-id:a;select-by-id:b;select-by-id:c;"
        "object-unlink-clones;object-to-path"
    )
    assert "select-all" not in actions


def test_conversion_actions_without_ids_selects_all():
    expected = "select-all;object-unlink-clones;object-to-path"
    assert selection.conversion_actions(None) == expected
    assert selection.conversion_actions([]) == expected


def test_ids_still_present_keeps_a_surviving_group():
    root = etree.fromstring(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<g id="label"><path id="label-path" d="M 0 0 L 1 1"/></g>'
        '<path id="box" d="M 0 0 L 1 0 L 1 1 Z"/>'
        '</svg>'
    )
    assert selection.ids_still_present(
        root, ["gone", "label", "box"]
    ) == ["label", "box"]


TEXT_BESIDE_PATH = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" id="root" width="440px" height="440px">
  <g id="layer">
    <path id="path-a" d="M 0 0 L 40 0 L 40 40 L 0 40 Z"/>
    <text id="label" x="200" y="20">Title</text>
  </g>
</svg>
"""

GROUP_WITH_TEXT = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" id="root">
  <g id="group-t"><text id="inner">Hi</text></g>
</svg>
"""


def test_unselected_text_does_not_abort_the_selection():
    doc = QtSvgDoc(TEXT_BESIDE_PATH, ids=["path-a"])
    assert regions(doc) == {"path-a"}


def test_selected_text_is_still_an_error():
    with pytest.raises(ValueError):
        QtSvgDoc(TEXT_BESIDE_PATH, ids=["label"])


def test_text_inside_a_selected_group_is_still_an_error():
    with pytest.raises(ValueError):
        QtSvgDoc(GROUP_WITH_TEXT, ids=["group-t"])


def test_contains_text_sees_a_descendant_and_ignores_paths():
    group_with_text = etree.fromstring(
        '<g xmlns="http://www.w3.org/2000/svg" id="g">'
        '<text id="t">hi</text>'
        '</g>'
    )
    nested_text = etree.fromstring(
        '<g xmlns="http://www.w3.org/2000/svg" id="g">'
        '<g id="inner"><text id="t">hi</text></g>'
        '</g>'
    )
    group_of_paths = etree.fromstring(
        '<g xmlns="http://www.w3.org/2000/svg" id="g">'
        '<path id="p" d="M 0 0 L 1 1"/>'
        '</g>'
    )
    assert selection.contains_text([group_with_text])
    assert selection.contains_text([nested_text])
    assert not selection.contains_text([group_of_paths])
