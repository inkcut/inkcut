"""
Copyright (c) 2022, Kārlis Seņko.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Oct 16, 2022

@author: karliss
"""
from math import sqrt
from atom.api import Float, Enum, Instance
from enaml.qt.QtCore import QPointF, QLineF
from enaml.qt.QtGui import QPainterPath, QVector2D
from inkcut.device.plugin import DeviceFilter, Model
from inkcut.core.utils import unit_conversions, log


# Element types
MoveToElement = QPainterPath.MoveToElement
LineToElement = QPainterPath.LineToElement
CurveToElement = QPainterPath.CurveToElement
CurveToDataElement = QPainterPath.CurveToDataElement

class MinLineConfig(Model):
    #: Units for display
    units = Enum(*unit_conversions.keys()).tag(config=True)

    # measured in 1/90inch like most other inkcut distances

    # don't lift the pen for distnaces shorter than this
    min_jump = Float(strict=False).tag(config=True)
    # avoid unnecesary slowdowns by blade offset making half circle on very short lines
    # connecting two bigger curves
    min_shift = Float(strict=False).tag(config=True)
    # remove edges shorter than this, might help if resulting file is too big/contains too many points
    min_edge = Float(strict=False).tag(config=True)

    def _default_units(self):
        return 'mm'


class MinLineFilter(DeviceFilter):
    #: Change config
    config = Instance(MinLineConfig, ()).tag(config=True)

    def apply_to_model(self, model, job):
        log.debug("apply minline filter", stack_info=False)
        if self.config.min_jump > 0:
            model = self.apply_min_jump(model)
        if self.config.min_edge > 0:
            model = self.apply_min_edge(model)
        if self.config.min_shift > 0:
            model = self.apply_min_shift(model)
        return model

    def apply_min_jump(self, model):
        result = []
        last_pos = None
        min_jump_sq = self.config.min_jump * self.config.min_jump
        for i in range(model.elementCount()):
            e = model.elementAt(i)
            if e.type == MoveToElement and last_pos is not None:
                p1 = QVector2D(e.x, e.y)
                d = p1 - last_pos
                if d.lengthSquared() < min_jump_sq:
                    continue
            result.append(e)
            last_pos = QVector2D(e.x, e.y)

        return self.path_from_items(result)
    
    def apply_min_edge(self, model):
        result = []
        last_pos = None
        min_d_sq = self.config.min_edge * self.config.min_edge
        for i in range(model.elementCount()):
            e = model.elementAt(i)
            if e.type == LineToElement and last_pos is not None and \
               i + 1 < model.elementCount() and model.elementAt(i+1).type != MoveToElement:
                p1 = QVector2D(e.x, e.y)
                d = p1 - last_pos
                if d.lengthSquared() < min_d_sq:
                    continue
            result.append(e)
            last_pos = QVector2D(e.x, e.y)

        return MinLineFilter.path_from_items(result)


    @staticmethod
    def normalize_angle(angle):
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle

    def apply_min_shift(self, model):
        min_d_sq = self.config.min_shift * self.config.min_shift

        last_angle = None

        result = QPainterPath()
        tmp_path = QPainterPath()
        ANGLE_CONFIG = 90

        def abs_angle(a1, a2):
            return abs(MinLineFilter.normalize_angle(a1 - a2))

        for i in range(model.elementCount()):
            e = model.elementAt(i)
            if e.type == MoveToElement:
                MinLineFilter.add_item_to_path(result, e, i, model)
                last_angle = None
            elif e.type == LineToElement:
                p = QPointF(e.x, e.y)
                segment = p - result.currentPosition()
                add = True

                segment_l2 = QPointF.dotProduct(segment, segment)
                if last_angle is not None and i + 1 < model.elementCount() and\
                        segment_l2  < min_d_sq:
                    next_element = model.elementAt(i + 1)
                    if next_element.type != MoveToElement and next_element.type != CurveToDataElement:
                        tmp_path.clear()
                        tmp_path.moveTo(p)
                        MinLineFilter.add_item_to_path(tmp_path, next_element, i+1, model)
                        angle_next = tmp_path.angleAtPercent(0)

                        if segment_l2 > 0:
                            angle_current = QLineF(result.currentPosition(), p).angle()
                            if abs_angle(angle_current, last_angle) + abs_angle(angle_next, angle_current) >\
                                    abs_angle(angle_next, last_angle) + ANGLE_CONFIG:
                                add = False
                        else:
                            add = False

                if add:
                    result.lineTo(QPointF(e.x, e.y))
                    last_angle = result.angleAtPercent(1)
                else:
                    last_angle = None
            elif e.type == CurveToDataElement:
                pass  # already processed
            else:
                MinLineFilter.add_item_to_path(result, e, i, model)
                last_angle = result.angleAtPercent(1)

        return result

    @staticmethod
    def add_item_to_path(result, e, i, items):
        if e.type == MoveToElement:
            result.moveTo(QPointF(e.x, e.y))
        elif e.type == LineToElement:
            result.lineTo(QPointF(e.x, e.y))
        elif e.type == CurveToElement:
            params = [QPointF(e.x, e.y)]
            j = i + 1
            while j < len(items) and items[j].type == CurveToDataElement:
                params.append(QPointF(items[j].x, items[j].y))
                j += 1
            if len(params) == 2:
                result.quadTo(*params)
            elif len(params) == 3:
                result.cubicTo(*params)
            else:
                raise ValueError("Invalid curve parameters: {}".format(params))
        elif e.type == CurveToDataElement:
            pass  # already processed
        else:
            raise ValueError("Unexpected curve element type: {}".format(e.type))

    @staticmethod
    def path_from_items(items):
        """ Convert list of QPainterPath.Element to QPainterPath

        """
        result = QPainterPath()
        for i, e in enumerate(items):
            MinLineFilter.add_item_to_path(result, e, i, items)
        return result
