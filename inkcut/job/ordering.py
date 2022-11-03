"""
Copyright (c) 2018-2020, the Inkcut team.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 15, 2018

@author: jrm
"""
import sys
import itertools
import math
from time import time
from atom.api import Atom, Instance, Int, ForwardInstance, List
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

    @staticmethod
    def subpath_move_distance(p0, subpaths, limit=sys.maxsize):
        d = 0
        p = p0
        # Local ref saves a lookup per iter
        distance = QVector2D.distanceToPoint
        for sp in subpaths:
            d += distance(p, start_point(sp))
            if d > limit:
                break  # Over the limit already abort
            p = end_point(sp)
        d += distance(p, p0)
        return d


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


class KdTree(Atom):
    class Node(Atom):
        position = Instance(QVector2D)
        id = Int()
        count = Int(0)
        left = ForwardInstance(lambda: KdTree.Node)
        right = ForwardInstance(lambda: KdTree.Node)
        parent = ForwardInstance(lambda: KdTree.Node)

        def __init__(self, position, id):
            self.position = position
            self.id = id

    points = List(QVector2D)
    n = Int(0)
    nodes = List(Node)
    minp = Instance(QVector2D)
    maxp = Instance(QVector2D)
    root = Instance(Node)

    def __init__(self, points):
        self.points = points
        self.n = len(points)
        self.nodes = []
        if points:
            self.minp = QVector2D(points[0])
            self.maxp = QVector2D(points[0])
            for p in points:
                self.minp.setX(min(self.minp.x(), p.x()))
                self.minp.setY(min(self.minp.y(), p.y()))
                self.maxp.setX(max(self.maxp.x(), p.x()))
                self.maxp.setY(max(self.maxp.y(), p.y()))
        self.nodes = [KdTree.Node(p, i) for (i, p) in enumerate(self.points)]
        self.root = KdTree._recursive_build(self.nodes[:], 0, None)

    def _item_count(node):
        if node:
            return node.count
        return 0

    @staticmethod
    def _recursive_build(items, depth, parent):
        if not items:
            return None
        if depth & 1:
            items.sort(key=lambda v: v.position.y())
        else:
            items.sort(key=lambda v: v.position.x())

        m = len(items) // 2
        pivot = items[m]
        left, right = items[:m], items[m+1:]

        pivot.parent = parent
        pivot.left = KdTree._recursive_build(left, depth + 1, pivot)
        pivot.right = KdTree._recursive_build(right, depth + 1, pivot)
        pivot.count = 1
        pivot.count += KdTree._item_count(pivot.left)
        pivot.count += KdTree._item_count(pivot.right)
        return pivot

    def remove(self, id):
        if id < 0:
            return
        node = self.nodes[id]
        node.id = -1

        while node:
            node.count -= 1
            node = node.parent

    @staticmethod
    def recursive_find(target_pos, node, depth, minp, maxp, best):
        if node.id >= 0:
            d2 = (target_pos - node.position).lengthSquared()
            if d2 < best[1]:
                best[0] = node
                best[1] = d2

        first, second = node.left, node.right

        dx = ((depth & 1 ) == 0)
        if dx:
            split_position = node.position.x()
            target_v = target_pos.x()
            first_size = (minp, QVector2D(split_position, maxp.y()))
            second_size = (QVector2D(split_position, minp.y()), maxp)
        else:
            split_position = node.position.y()
            target_v = target_pos.y()
            first_size = (minp, QVector2D(maxp.x(), split_position))
            second_size = (QVector2D(minp.x(), split_position), maxp)

        if target_v >= split_position:
            first, second = second, first
            first_size, second_size = second_size, first_size

        if first and first.count:
            KdTree.recursive_find(target_pos, first, depth + 1, *first_size, best)
        if second and second.count:
            de = (target_v - split_position)
            de = de * de
            if dx:
                vy = max(0, minp.y() - target_pos.y()) + max(0, target_pos.y() - maxp.y())
                de += vy * vy
            else:
                vy = max(0, minp.x() - target_pos.x()) + max(0, target_pos.x() - maxp.x())
                de += vy * vy

            if de < best[1]:
                KdTree.recursive_find(target_pos, second, depth + 1, *second_size, best)

    def nearest_node(self, target_pos):
        best = [None, math.inf]
        KdTree.recursive_find(target_pos, self.root, 0, self.minp, self.maxp, best)
        return best[0]


def element_to_vec(element):
    return QVector2D(element.x, element.y)


def start_point(path):
    return element_to_vec(path.elementAt(0))


def end_point(path):
    return element_to_vec(path.elementAt(path.elementCount() - 1))


class OrderShortestPath(OrderHandler):
    """  Variation of greedy TSP solution using KDtree to query nearest point

    """
    name = QApplication.translate("job", "Shortest Path")

    def order(self, job, path):
        """ Sort subpaths by minimizing the distances between all start
        and end points.

        """
        subpaths = split_painter_path(path)
        log.debug("Subpath count: {}".format(len(subpaths)))

        if len(subpaths) <= 0:
            return path

        now = time()
        # This is in the UI thread
        time_limit = now + self.plugin.optimizer_timeout
        zero = QVector2D(0, 0)
        endpoints = []
        for sp in subpaths:
            start = start_point(sp)
            end = end_point(sp)
            endpoints.append(start)
            endpoints.append(end)

        point_tree = KdTree(endpoints)
        used = [False] * len(subpaths)
        original = subpaths
        result = []
        p = zero
        for i in range(len(subpaths)):
            idb = point_tree.nearest_node(p).id
            subpath_id = idb // 2
            # remove both ends
            point_tree.remove(idb)
            point_tree.remove(idb ^ 1)

            assert subpath_id >= 0
            assert not used[subpath_id]

            used[subpath_id] = True
            subpath = subpaths[subpath_id]
            if idb & 1:
                p = start_point(subpath)
                result.append(subpath.toReversed())
            else:
                p = end_point(subpath)
                result.append(subpath)

            if time() > time_limit:
                # At least part of it is optimized. Shouldn't happen
                # with a typical input.
                log.warning(
                    "Shortest path search aborted (time limit reached)")
                break
        else:
            log.debug("Shortest path processed all")
        
        result.extend([p for (i, p) in enumerate(subpaths) if not used[i]])

        duration = time() - now
        d = OrderHandler.subpath_move_distance(zero, original)
        d = d - OrderHandler.subpath_move_distance(zero, result)
        log.debug("Shortest path search: Saved {} in of movement in {}".format(
                to_unit(d, 'in'), duration))

        return join_painter_paths(result)

class SpaceFillingCurveOrder(OrderHandler):
    def curve_pos(self, p, p0, s):
        raise NotImplementedError 

    def order(self, job, path):
        bounds = path.boundingRect()
        max_size = max(bounds.size().width(), bounds.size().height())
        p0 = bounds.topLeft()
        res = self.order_by_func(
            job, path, lambda p: self.curve_pos(start_point(p), p0, max_size))
        return res


class OrderHilbert(SpaceFillingCurveOrder):
    name = QApplication.translate("job", 'SFC Hilbert')

    def curve_pos(self, p, p0, s):
        s *= 0.5
        p = p.toPointF() - p0
        x = p.x()
        y = p.y()
        result = 0
        STEPS = 32
        for i in range(STEPS): 
            bits = 0
            if x > s:
                bits = 1
                x -= s
                if y > s:
                    bits = 2
                    y -= s
            else:
                if y > s:
                    bits = 3
                    x, y = (s-(y-s), s-x)
                else:
                    x, y = (y, x)

            result = (result << 2) + bits
            s *= 0.5
        return result


class OrderZCurve(SpaceFillingCurveOrder):
    name = QApplication.translate("job", 'SFC Z-curve')

    def curve_pos(self, p, p0, s):
        p = p.toPointF() - p0
        x = p.x()
        y = p.y()
        result = 0
        STEPS = 32
        for i in range(STEPS): 
            bits = 0
            if y > s:
                y -= s
                bits += 2
            if x > s:
                x -= s
                bits += 1
            result = (result << 2) + bits
            s *= 0.5
        return result


#: Register all subclasses
REGISTRY = {c.name: c for c in find_subclasses(OrderHandler) if c.name}
