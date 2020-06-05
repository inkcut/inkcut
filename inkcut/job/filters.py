"""
Copyright (c) 2020, the Inkcut team.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on April 10, 2020

@author: jrm
"""
from atom.api import Atom, Unicode, Bool, Float
from enaml.colors import ColorMember, SVG_COLORS
from inkcut.core.svg import QtSvgDoc
from inkcut.core.utils import log, find_subclasses

NAMESPACES = {
    "inkscape": "http://www.inkscape.org/namespaces/inkscape",
    "svg": "http://www.w3.org/2000/svg",
}


# Reverse mapping of color
SVG_COLOR_NAMES = {"#%s" % hex(c.argb)[4:]: n for n, c in SVG_COLORS.items()}


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

        """
        raise NotImplementedError()



class LayerFilter(JobFilter):
    type = "layer"

    #: Offset to shift the layer
    offset_x = Float()
    offset_y = Float()

    @classmethod
    def get_filter_options(cls, job, doc):
        # TODO: Extract all layers in the document and return a list of them
        svg = doc._svg
        layers = []
        for g in svg.xpath('//*[@inkscape:groupmode="layer"]',
                           namespaces=NAMESPACES):
            label = g.attrib.get(
                '{http://www.inkscape.org/namespaces/inkscape}label')
            if label is not None:
                layers.append(LayerFilter(name=label))
        return layers

    def apply_filter(self, job, doc):
        # TODO: Remove this layer from the document
        return doc


class ColorFilter(JobFilter):
    type = "color"

    #: The color
    color = ColorMember()

    @classmethod
    def get_filter_options(cls, job, doc):
        svg = doc._svg
        colors = []
        for e in svg.xpath('//*[@style]'):
            style = e.attrib.get('style')
            if style is None:
                continue
            style = dict(it.split(":") for it in style.split(";"))
            stroke = style.get('stroke')
            if stroke is not None:
                # Try to look up a common name
                label = SVG_COLOR_NAMES.get(stroke.lower(), stroke)
                colors.append(ColorFilter(name=label, color=stroke))
        return colors

    def apply_filter(self, job, doc):
        # TODO: Remove this color from the document
        return doc



#: Register all subclasses
REGISTRY = {c.type: c for c in find_subclasses(JobFilter)}
