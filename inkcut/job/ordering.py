"""
Copyright (c) 2018, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 15, 2018

@author: jrm
"""
import itertools
from time import time
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


class OrderMinWidth(OrderHandler):
    name = 'Min width'

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: p.boundingRect().width())


class OrderMaxWidth(OrderHandler):
    name = 'Max width'

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: -p.boundingRect().width())


class OrderMinHeight(OrderHandler):
    name = 'Min height'

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: p.boundingRect().height())


class OrderMaxHeight(OrderHandler):
    name = 'Max height'

    def order(self, job, path):
        return self.order_by_func(
            job, path, lambda p: -p.boundingRect().height())


class OrderShortestPath(OrderHandler):
    """  This is a very stupid shortest path search that brute force goes
    through each iteration until time runs out.
    
    """
    name = 'Shortest Path'
    time_limit = 0.2  # This is in the UI thread
    
    
    def order(self, job, path):
        """ Sort subpaths by minimizing the distances between all start
        and end points.
        
        """
        subpaths = split_painter_path(path)
        
        # If the actual distance is longer than this you're screwed anyways
        d = 9999999999999999999999
        shortest = subpaths
        time_limit = time()+self.time_limit
        
        # Cache all start and end points
        zero = QVector2D(0, 0)
        for sp in subpaths:
            # Save start and end points
            start = sp.elementAt(0)
            end = sp.elementAt(sp.elementCount()-1)
            sp.start_point = QVector2D(start.x, start.y)
            sp.end_point = QVector2D(end.x, end.y)
            
        i = 0
        # TODO: This is a "stupid" search
        path_distance = self.subpath_move_distance
        for sp in itertools.permutations(subpaths):
            l = path_distance(zero, sp, d)
            if l < d:
                d = l
                shortest = sp
            i += 1
            # time.time() is slow so limit the calls
            if i > 1000 and time() > time_limit:
                break
        log.debug("Shortest path search: {} in {} iterations".format(
            to_unit(d, 'in'), i))
        return join_painter_paths(shortest)
    
    def subpath_move_distance(self, p, subpaths, limit):
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


#: Register all sublcasses
REGISTRY = {c.name: c for c in find_sublcasses(OrderHandler)}
