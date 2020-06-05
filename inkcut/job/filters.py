"""
Copyright (c) 2020, the Inkcut team.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on April 10, 2020

@author: jrm
"""
import copy
from lxml import etree
from atom.api import Atom, Unicode, Instance, Bool, Float
from enaml.colors import ColorMember, SVG_COLORS
from inkcut.core.svg import QtSvgDoc, EtreeElement
from inkcut.core.utils import (
    log, find_subclasses, split_painter_path, join_painter_paths
)

NAMESPACES = {
    "inkscape": "http://www.inkscape.org/namespaces/inkscape",
    "svg": "http://www.w3.org/2000/svg",
}


# Reverse mapping of color
SVG_COLOR_NAMES = {"#%s" % hex(c.argb)[4:]: n for n, c in SVG_COLORS.items()}


def get_node_style(e):
    """ Retrun the parsed style of an svg node

    """
    style = e.attrib.get('style')
    if style is None:
        return {}
    return dict(it.split(":") for it in style.split(";"))


def get_layers(svg):
    pattern = '//*[@inkscape:groupmode="layer"]'
    return svg.xpath(pattern, namespaces=NAMESPACES)


def get_layer_label(g):
    attr = '{http://www.inkscape.org/namespaces/inkscape}label'
    return g.attrib.get(attr)


class JobFilter(Atom):
    #: A fixed type name for the UI to extract without using isinstance
    type = ""

    #: Name to display in the UI
    name = Unicode()

    #: If NOT enabled then apply_filter is called which should return the
    #: path with the filtered path elements REMOVED.
    enabled = Bool(True)

    @classmethod
    def get_filter_options(cls, job, doc):
        """ Get the list of options that can be filtered from the document

        Parameters
        ----------
        job: inkcut.models.Job
            The job that is being processed. This should only be used to
            reference settings.
        doc: QtSvgDoc
            The document to filter.

        Returns
        -------
        results: List[cls]
            The list of filterable options to choose from.

        """
        raise NotImplementedError()

    def apply_filter(self, job, doc):
        """ Apply the filter to the path by removing paths that are excluded
        by this filter.  This is only called if the `enabled` is set to false.

        Parameters
        ----------
        job: inkcut.models.Job
            The job that is being processed. This should only be used to
            reference settings.
        doc: QtSvgDoc
            The document to filter.

        Returns
        -------
        doc: QtSvgDoc
            The filtered document.

        """
        raise NotImplementedError()


class LayerFilter(JobFilter):
    type = "layer"

    layer = Instance(EtreeElement)

    #: Offset to shift the layer
    offset_x = Float()
    offset_y = Float()

    @classmethod
    def get_filter_options(cls, job, doc):
        # TODO: Extract all layers in the document and return a list of them
        svg = doc._svg
        layers = []
        for g in get_layers(svg):
            label = get_layer_label(g)
            if label is not None:
                layers.append(LayerFilter(name=label, layer=g))
        return layers

    def apply_filter(self, job, doc):
        """ Remove all subpaths from doc that are in this layer by reparsing
        the xml.
        """
        # Copy it since we're modifying
        svg = copy.deepcopy(doc._svg)

        # Find the layer in the cloned doc
        for g in get_layers(svg):
            label = get_layer_label(g)
            if label == self.name:
                g.getparent().remove(g)
                break

        return QtSvgDoc(svg)


class FillColorFilter(JobFilter):
    type = "fill-color"
    style_attr = 'fill'

    #: The color
    color = ColorMember()

    #: The color name
    data = Unicode()

    @classmethod
    def get_filter_options(cls, job, doc):
        svg = doc._svg
        colors = []
        for e in svg.xpath('//*[@style]'):
            style = get_node_style(e)
            color = style.get(cls.style_attr)
            if color is not None:
                # Try to look up a common name
                label = SVG_COLOR_NAMES.get(color.lower(), color)
                colors.append(cls(name=label, color=color, data=color))
        return colors

    def apply_filter(self, job, doc):
        """ Remove all subpaths from doc that are in this layer by reparsing
        the xml.
        """
        # Copy it since we're modifying
        svg = copy.deepcopy(doc._svg)

        # Remove all nodes with that stroke style
        for e in svg.xpath('//*[@style]'):
            style = get_node_style(e)
            if style.get(self.style_attr) == self.data:
                e.getparent().remove(e)

        return QtSvgDoc(svg)


class StrokeColorFilter(FillColorFilter):
    type = 'stroke-color'
    style_attr = 'stroke'


#: Register all subclasses
REGISTRY = {c.type: c for c in find_subclasses(JobFilter)}
