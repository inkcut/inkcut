"""
Copyright (c) 2020, the Inkcut team.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on April 10, 2020

@author: jrm
"""
import copy
from lxml import etree
from atom.api import Atom, Str, Instance, Bool, Float
from enaml.colors import Color, ColorMember, SVG_COLORS
from inkcut.core.svg import QtSvgDoc, EtreeElement
from enaml.qt.QtGui import QPainterPath, QPolygonF
from enaml.qt.QtCore import QPointF
from inkcut.core.utils import (
    log, find_subclasses, split_painter_path, join_painter_paths
)

NAMESPACES = {
    "inkscape": "http://www.inkscape.org/namespaces/inkscape",
    "svg": "http://www.w3.org/2000/svg",
}


# Reverse mapping of color
SVG_COLOR_NAMES = {"#%s" % hex(c.argb)[4:]: n for n, c in SVG_COLORS.items()}
SVG_COLOR_NAMES['none'] = 'transparent'


def get_node_style(e):
    """ Retrun the parsed style of an svg node

    """
    style = e.attrib.get('style')
    if style is None:
        return {}
    return dict(it.split(":") if ":" in it else (it, None)
                for it in style.split(";"))


def get_layers(svg):
    pattern = '//*[@inkscape:groupmode="layer"]'
    return svg.xpath(pattern, namespaces=NAMESPACES)


def get_layer_label(g):
    attr = '{http://www.inkscape.org/namespaces/inkscape}label'
    return g.attrib.get(attr)


class Filter(Atom):
    #: A fixed type name for the UI to extract without using isinstance
    type = ""

    #: Name to display in the UI
    name = Str()

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

# These filters receive an SVG document
# and produce a filtered version of that
# same SVG document after filtering/modifying
# based on the SVG document structure and
# attributes.
class SvgFilter(Filter):
    pass

# These filters receive a general PainterPath
# and filter/modify based on geometry rather than
# SVG structure which is lost when we start manipulating
# the geometry instead of the SVG/XML structure
class PathFilter(Filter):
    pass

# This filter clips the geometry to the
# bounding-box implied by the Job's material
# settings.  This helps prevent us from accidentally
# sending the plotter head off the gantry trying to
# draw geometry that is invalid for the material/device.
class ClipFilter(PathFilter):
    @classmethod
    def get_filter_options(cls, job, doc):
        # This filter is always 'enabled' but that
        # just means it will always run.
        # It may clip or not clip depending on whether
        # the job's clip_to_plot_area is true.  This is because
        # the get_filter_options is only called when
        # the document is loaded, but not when options
        # are checked by the user.
        return [cls(enabled=False)]

    def apply_filter(self, job, doc):
        # If it's not enabled by the user, we do nothing.
        if not job.clip_to_plot_area:
            return doc

        # We first get the boundary of the page.
        clip_x0 = job.material.padding_left
        clip_y0 = job.material.padding_bottom
        clip_x1 = job.material.width() - job.material.padding_right
        clip_y1 = job.material.height() - job.material.padding_top

        # Then we assemble this as a list of points
        clip_points = [
            QPointF(clip_x0, clip_y0),
            QPointF(clip_x1, clip_y0),
            QPointF(clip_x1, clip_y1),
            QPointF(clip_x0, clip_y1),
            QPointF(clip_x0, clip_y0)
        ]

        # And finally turn this into a polygon
        # and then a painter path
        clip_polygon = QPolygonF(clip_points)
        clip_path = QPainterPath()
        clip_path.addPolygon(clip_polygon)

        # Finally, we do the work of clipping
        # so we can remove the un-needed pieces.
        # It is important that the clip happen
        # before the optimize path because
        # removing path segments would change
        # the optimizer's results
        clipped = doc.intersected(clip_path)

        return clipped
        
class LayerFilter(SvgFilter):
    type = "layer"

    layer = Instance(EtreeElement)

    #: Offset to shift the layer
    offset_x = Float()
    offset_y = Float()

    @classmethod
    def get_filter_options(cls, job, doc):
        # TODO: Extract all layers in the document and return a list of them
        svg = doc._e
        layers = []
        for g in get_layers(svg):
            label = get_layer_label(g)
            if label is not None:
                style = get_node_style(g)
                # If the layer is hidden disable it by default
                enabled = style.get('display') != "none"
                layers.append(cls(name=label, layer=g, enabled=enabled))
        return layers

    def apply_filter(self, job, doc):
        """ Remove all subpaths from doc that are in this layer by reparsing
        the xml.
        """
        # Copy it since we're modifying
        svg = copy.deepcopy(doc._e)

        # Find the layer in the cloned doc
        for g in get_layers(svg):
            label = get_layer_label(g)
            if label == self.name:
                g.getparent().remove(g)
                break

        return QtSvgDoc(svg, parent=True)


class FillColorFilter(SvgFilter):
    type = "fill-color"
    style_attr = 'fill'

    #: The color
    color = ColorMember()

    #: The color name
    data = Str()

    @classmethod
    def get_filter_options(cls, job, doc):
        svg = doc._e
        colors = []
        used = set()
        for e in svg.xpath('//*[@style]'):
            style = get_node_style(e)
            color = style.get(cls.style_attr)
            if color is not None and color not in used:
                used.add(color)
                # Try to look up a common name
                label = SVG_COLOR_NAMES.get(color.lower(), color)
                colors.append(cls(name=label, color=color, data=color))
        return colors

    def apply_filter(self, job, doc):
        """ Remove all subpaths from doc that are in this layer by reparsing
        the xml.
        """
        # Copy it since we're modifying
        svg = copy.deepcopy(doc._e)

        # Remove all nodes with that stroke style
        for e in svg.xpath('//*[@style]'):
            style = get_node_style(e)
            if style.get(self.style_attr) == self.data:
                e.getparent().remove(e)

        return QtSvgDoc(svg, parent=True)


class StrokeColorFilter(FillColorFilter):
    type = 'stroke-color'
    style_attr = 'stroke'


#: Register all subclasses
# Note that we distinguish between SVG filters
# and Path filters because path filters do NOT
# preserve the SVG tags since they can alter
# geometry irrespective of the XML structure of the document.
SVG_FILTERS = {c.type: c for c in find_subclasses(SvgFilter)}
PATH_FILTERS = {c.type: c for c in find_subclasses(PathFilter)}
