"""
Copyright (c) 2018-2020, the Inkcut team.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 15, 2018

@author: jrm
"""
import sys
import itertools
from time import time
from atom.api import Atom, Instance
from enaml.qt.QtCore import QPointF
from enaml.qt.QtGui import QVector2D
from enaml.qt.QtWidgets import QApplication
from inkcut.core.utils import (
    log, split_painter_path, join_painter_paths, to_unit, find_subclasses
)

from inkcut.core.api import Plugin
from inkcut.core.workbench import InkcutWorkbench


class OrderHandler(Atom):
    name = ''

    #: A reference to the JobPlugin
    plugin = Instance(Plugin)

    def _default_plugin(self):
        workbench = InkcutWorkbench.instance()
        return workbench.get_plugin("inkcut.job")

    def order_by_func(self, job, path, sort_func):
        subpaths = sorted(split_painter_path(path), key=sort_func)
        return join_painter_paths(subpaths)

    def order(self, job, path):
        """ Adjust the cutting order of the job's paths.

        Parameters
        ----------
        job: inkcut.models.Job
            The job that is being processed. This should only be used to
            reference settings.
        path: QPainterPath
            The path model to re-order.

        """
        raise NotImplementedError()


class OrderNormal(OrderHandler):
    name = QApplication.translate("job", "Normal")

    def order(self, job, path):
        return path


class OrderReversed(OrderHandler):
    name = QApplication.translate("job", "Reversed")
    def order(self, job, path):
        return path.toReversed()


class OrderMinX(OrderHandler):
    name = QApplication.translate("job", 'Min X')

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: p.boundingRect().left())


class OrderMaxX(OrderHandler):
    name = QApplication.translate("job", 'Max X')

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: p.boundingRect().right())


class OrderMinY(OrderHandler):
    name = QApplication.translate("job", 'Min Y')

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: p.boundingRect().bottom())


class OrderMaxY(OrderHandler):
    name = QApplication.translate("job", 'Max Y')

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: p.boundingRect().top())


class OrderShortestPath(OrderHandler):
    """  This uses Dijkstra's algorithm to find the shortest path.

    """
    name = QApplication.translate("job", "Shortest Path")

    def order(self, job, path):
        """ Sort subpaths by minimizing the distances between all start
        and end points.

        """
        subpaths = split_painter_path(path)
        log.debug("Subpath count: {}".format(len(subpaths)))

        # Cache all start and end points
        now = time()
        # This is in the UI thread
        time_limit = now + self.plugin.optimizer_timeout
        zero = QVector2D(0, 0)
        for sp in subpaths:
            # Average start and end into one "vertex"
            start = sp.elementAt(0)
            end = sp.elementAt(sp.elementCount()-1)
            sp.start_point = QVector2D(start.x, start.y)
            sp.end_point = QVector2D(end.x, end.y)

        distance = QVector2D.distanceToPoint
        original = subpaths[:]
        result = []
        p = zero
        while subpaths:
            best = sys.maxsize
            shortest = None
            for sp in subpaths:
                d = distance(p, sp.start_point)
                if d < best:
                    best = d
                    shortest = sp

            p = shortest.end_point
            result.append(shortest)
            subpaths.remove(shortest)

            # time.time() is slow so limit the calls
            if time() > time_limit:
                result.extend(subpaths)  # At least part of it is optimized
                log.warning(
                    "Shortest path search aborted (time limit reached)")
                break

        duration = now - time()
        d = self.subpath_move_distance(zero, original)
        d = d - self.subpath_move_distance(zero, result)
        log.debug("Shortest path search: Saved {} in of movement in {}".format(
                to_unit(d, 'in'), duration))
        return join_painter_paths(result)

    def subpath_move_distance(self, p, subpaths, limit=sys.maxsize):
        # Collect start and end points
        d = 0

        # Local ref saves a lookup per iter
        distance = QVector2D.distanceToPoint
        for sp in subpaths:
            d += distance(p, sp.start_point)
            if d > limit:
                break  # Over the limit already abort
            p = sp.end_point
        return d


#: Register all subclasses
REGISTRY = {c.name: c for c in find_subclasses(OrderHandler)}
