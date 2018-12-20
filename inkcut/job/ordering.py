"""
Copyright (c) 2018, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 15, 2018

@author: jrm
"""
import sys
import itertools
from time import time
from enaml.qt.QtCore import QPointF
from enaml.qt.QtGui import QVector2D
from inkcut.core.utils import (
    log, split_painter_path, join_painter_paths, to_unit
)


class OrderHandler(object):
    name = ''
    
    def order_by_func(self, job, path, sort_func):
        subpaths = sorted(split_painter_path(path), key=sort_func)
        return join_painter_paths(subpaths)
    
    def order(self, job, path):
        raise NotImplementedError()


class OrderNormal(OrderHandler):
    name = 'Normal'

    def order(self, job, path):
        return path


class OrderReversed(OrderHandler):
    name = 'Reversed'

    def order(self, job, path):
        return path.toReversed()


class OrderMinX(OrderHandler):
    name = 'Min X'

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: p.boundingRect().left())


class OrderMaxX(OrderHandler):
    name = 'Max X'

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: p.boundingRect().right())


class OrderMinY(OrderHandler):
    name = 'Min Y'

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: p.boundingRect().bottom())


class OrderMaxY(OrderHandler):
    name = 'Max Y'

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: p.boundingRect().top())

    
class OrderShortestPath(OrderHandler):
    """  This uses Dijkstra's algorithm to find the shortest path.
    
    """
    name = 'Shortest Path'
    time_limit = 0.2  # This is in the UI thread
    
    def order(self, job, path):
        """ Sort subpaths by minimizing the distances between all start
        and end points.
        
        """
        subpaths = split_painter_path(path)
        log.debug("Subpath count: {}".format(len(subpaths)))
        
        # Cache all start and end points
        time_limit = time()+self.time_limit
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
            best = sys.maxint
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
                log.debug("Shortest path search aborted (time limit reached)")
                break
        d = self.subpath_move_distance(zero, original)
        d = d-self.subpath_move_distance(zero, result)
        log.debug("Shortest path search: Saved {} in of movement ".format(
            to_unit(d, 'in')))
        return join_painter_paths(result)
    
    def subpath_move_distance(self, p, subpaths, limit=sys.maxint):
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
    
    
def find_sublcasses(cls):
    """ Finds all known (imported) subclasses of the given class """
    cmds = []
    for subclass in cls.__subclasses__():
        cmds.append(subclass)
        cmds.extend(find_sublcasses(subclass))
    return cmds


#: Register all subclasses
REGISTRY = {c.name: c for c in find_sublcasses(OrderHandler)}
