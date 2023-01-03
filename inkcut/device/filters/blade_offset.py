"""
Copyright (c) 2018-2019, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 14, 2018
Rewrote on June 8, 2019

@author: jrm
"""
from math import sqrt, cos, sin, radians, isinf, pi, isnan
from atom.api import Float, Enum, Instance
from enaml.qt.QtCore import QPointF, QRectF, QSizeF
from enaml.qt.QtGui import QPainterPath, QTransform, QVector2D

from inkcut.device.plugin import DeviceFilter, Model
from inkcut.core.utils import unit_conversions, log, trailing_angle


# Element types
MoveToElement = QPainterPath.MoveToElement
LineToElement = QPainterPath.LineToElement
CurveToElement = QPainterPath.CurveToElement
CurveToDataElement = QPainterPath.CurveToDataElement


IDENITY_MATRIX = QTransform.fromScale(1, 1)


def fp(point):
    return "({}, {})".format(round(point.x(), 3), round(point.y(), 3))


class BladeOffsetConfig(Model):
    #: BladeOffset in user units
    offset = Float(strict=False).tag(config=True)

    #: Units for display
    offset_units = Enum(*unit_conversions.keys()).tag(config=True)

    #: If the angle is less than this, consider it continuous
    cutoff = Float(5.0, strict=False).tag(config=True)

    def _default_offset_units(self):
        return 'mm'


class BladeOffsetFilter(DeviceFilter):
    #: Change config
    config = Instance(BladeOffsetConfig, ()).tag(config=True)

    def apply_to_model(self, model, job):
        """ Apply the filter to the path model.

        Parameters
        ----------
        model: QPainterPath
            The path to process
        job: inkcut.device.Job
            The job this is coming from

        Returns
        -------
        model: QPainterPath
            The modified path

        """
        d = self.config.offset
        if d <= 0:
            return model
        return self.apply_blade_offset(model, job)

    def apply_blade_offset(self, path, job):
        """ Apply blade offset to the given path.

        """
        params = []
        e = None
        cmd = None
        qf = getattr(job.config, 'quality_factor', 1)

        # Holds the blade path
        blade_path = QPainterPath()
        offset_path = QPainterPath()

        def finish_curve():
            n = len(params)
            if n == 2:
                self.process_quad(offset_path, blade_path, params, qf)
            elif n == 3:
                self.process_cubic(offset_path, blade_path, params, qf)
            else:
                raise ValueError("Unexpected curve data length %s" % n)

        for i in range(path.elementCount()):
            e = path.elementAt(i)

            # Finish the previous curve (if there was one)
            if cmd == CurveToElement and e.type != CurveToDataElement:
                finish_curve()
                params = []

            # Reconstruct the path
            if e.type == MoveToElement:
                cmd = MoveToElement
                self.process_move(offset_path, blade_path, [QPointF(e.x, e.y)])
            elif e.type == LineToElement:
                cmd = LineToElement
                self.process_line(offset_path, blade_path, [QPointF(e.x, e.y)])
            elif e.type == CurveToElement:
                cmd = CurveToElement
                params = [QPointF(e.x, e.y)]
            elif e.type == CurveToDataElement:
                params.append(QPointF(e.x, e.y))

        # Finish the previous curve (if there was one)
        if params:
            finish_curve()
        return offset_path

    def add_continuity_correction(self, offset_path, blade_path, point):
        """ Adds if the upcoming angle and previous angle are not the same
        we need to correct for that difference by "arcing back" about the
        current blade point with a radius equal to the offset.

        """
        # Current blade position
        cur = blade_path.currentPosition()

        # Determine direction of next move
        sp = QPainterPath()
        sp.moveTo(cur)
        sp.lineTo(point)
        next_angle = sp.angleAtPercent(1)

        # Direction of last move
        angle = trailing_angle(blade_path)

        # If not continuous it needs corrected with an arc
        if isnan(angle) or isnan(next_angle):
            return
        if abs(angle - next_angle) > self.config.cutoff:
            r = self.config.offset
            circle_size = QPointF(r, r)
            diff = next_angle - angle
            if diff > 180:
                diff -= 360
            if diff < -180:
                diff += 360
            offset_path.arcTo(QRectF(cur - circle_size, QSizeF(2 * r, 2 * r)), angle, diff)
            # This works for small offsets < 0.5 mm
            #offset_path.lineTo(po)


    def process_move(self, offset_path, blade_path, params):
        """ Adjust the start point of a move by the blade offset. When just
        starting we don't know the blade angle so no correction is done.

        """
        r = self.config.offset
        p0 = params[0]

        # Get direction of last move
        blade_path.moveTo(p0)
        angle = trailing_angle(blade_path)

        if isnan(angle):
            dx, dy = 0, r
        else:
            a = radians(angle)
            dx, dy = r*cos(a), -r*sin(a)

        po = QPointF(p0.x()+dx, p0.y()+dy)
        offset_path.moveTo(po)

    def process_line(self, offset_path, blade_path, params):
        """ Correct continuity and adjust the end point of the line to end
        at the correct spot.
        """
        r = self.config.offset
        p0 = params[0]
        self.add_continuity_correction(offset_path, blade_path, p0)
        blade_path.lineTo(p0)  # Must be done after continuity correction!
        angle = trailing_angle(blade_path)

        if isnan(angle):
            dx, dy = 0, r
        else:
            a = radians(angle)
            dx, dy = r*cos(a), -r*sin(a)

        po = QPointF(p0.x()+dx, p0.y()+dy)
        offset_path.lineTo(po)

    def process_quad(self, offset_path, blade_path, params, quality):
        """ Add offset correction to a quadratic bezier.
        """
        r = self.config.offset
        p0 = blade_path.currentPosition()
        p1, p2 = params
        self.add_continuity_correction(offset_path, blade_path, p1)

        curve = QPainterPath()
        curve.moveTo(p0)
        curve.quadTo(*params)
        p = QPainterPath()
        p.moveTo(p0)

        if quality == 1:
            polygon = curve.toSubpathPolygons(IDENITY_MATRIX)[0]
        else:
            m = QTransform.fromScale(quality, quality)
            m_inv = QTransform.fromScale(1/quality, 1/quality)
            polygon = m_inv.map(curve.toSubpathPolygons(m)[0])

        for point in polygon:
            p.lineTo(point)
            t = curve.percentAtLength(p.length())
            angle = curve.angleAtPercent(t)
            a = radians(angle)
            dx, dy = r*cos(a), -r*sin(a)
            offset_path.lineTo(point.x()+dx, point.y()+dy)

        blade_path.quadTo(*params)

    def process_cubic(self, offset_path, blade_path, params, quality):
        """ Add offset correction to a cubic bezier.
        """
        r = self.config.offset
        p0 = blade_path.currentPosition()
        p1, p2, p3 = params
        self.add_continuity_correction(offset_path, blade_path, p1)

        curve = QPainterPath()
        curve.moveTo(p0)
        curve.cubicTo(*params)
        p = QPainterPath()
        p.moveTo(p0)

        if quality == 1:
            polygon = curve.toSubpathPolygons(IDENITY_MATRIX)[0]
        else:
            m = QTransform.fromScale(quality, quality)
            m_inv = QTransform.fromScale(1/quality, 1/quality)
            polygon = m_inv.map(curve.toSubpathPolygons(m)[0])

        for point in polygon:
            p.lineTo(point)
            t = curve.percentAtLength(p.length())
            angle = curve.angleAtPercent(t)
            a = radians(angle)
            dx, dy = r*cos(a), -r*sin(a)
            offset_path.lineTo(point.x()+dx, point.y()+dy)

        blade_path.cubicTo(*params)
