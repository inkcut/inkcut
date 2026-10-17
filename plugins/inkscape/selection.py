# -*- coding: utf-8 -*-
"""Selection helpers shared by the Inkscape extensions. No inkex import."""


def id_breaks_actions(node_id):
    # Inkscape joins actions with ';'. A newline breaks the same string.
    return ";" in node_id or "\n" in node_id or "\r" in node_id


def conversion_actions(ids=None):
    """Inkscape --actions value. No ids converts the whole document."""
    tail = "object-unlink-clones;object-to-path"
    if not ids:
        return "select-all;" + tail
    selects = ";".join("select-by-id:%s" % node_id for node_id in ids)
    return selects + ";" + tail


def ids_still_present(root, ids):
    """Original ids that still exist on an element, in the same order."""
    present = set()
    for element in root.iter():
        element_id = element.get("id")
        if element_id:
            present.add(element_id)
    return [element_id for element_id in ids if element_id in present]


def _local_name(node):
    tag = getattr(node, "tag", None)
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def contains_text(nodes):
    """True when a node, or any element inside it, is text."""
    for node in nodes:
        iterate = getattr(node, "iter", None)
        elements = iterate() if iterate is not None else (node,)
        for element in elements:
            if _local_name(element) == "text":
                return True
    return False
