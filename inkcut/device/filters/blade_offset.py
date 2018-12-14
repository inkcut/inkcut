"""
Copyright (c) 2018, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 14, 2018

@author: jrm
"""
from math import sqrt, cos, radians, isinf
from atom.api import Float, Enum, Instance
from inkcut.device.plugin import DeviceFilter, Model
from inkcut.core.utils import unit_conversions
from enaml.qt.QtGui import QPainterPath, QTransform, QVector2D


IDENITY_MATRIX = QTransform.fromScale(1, 1)


class BladeOffsetConfig(Model):
    #: BladeOffset in user units
    offset = Float(strict=False).tag(config=True)
    
    #: Units for display 
    offset_units = Enum(*unit_conversions.keys()).tag(config=True)
    
    #: Cutoff angle
    cutoff = Float(20.0, strict=False).tag(config=True)
    
    def _default_offset_units(self):
        return 'mm'


class BladeOffsetFilter(DeviceFilter):
    #: Change config
    config = Instance(BladeOffsetConfig, ()).tag(config=True)
    
    def apply_to_polypath(self, polypath):
        """ Apply the filter to the polypath. It's much easier doing this
        after conversion to polypaths.
        
        Parameters
        ----------
        polypath: List of QPolygon
            List of polygons to process
        
        Returns
        -------
        polypath: List of QPolygon
            List of polygons with the filter applied
        
        """
        d = self.config.offset
        if d <= 0:
            return polypath
        
        result = []
        for poly in polypath:
            result.extend(self.apply_blade_offset(poly, d))
        
        return result
    
    def apply_blade_offset(self, poly, offset):
        """ Apply blade offset to the given polygon by appending a quadratic
        bezier to each point .
        
        """
        # Use a QPainterPath to track the distance in c++
        path = QPainterPath()
        cutoff = cos(radians(self.config.cutoff)) # Forget 
        last = None
        n = len(poly)
        for i, p in enumerate(poly):
            if i == 0:
                path.moveTo(p)
                last_path = QPainterPath()
                last_path.moveTo(p)
                last = p
                continue
            
            # Move to the point
            path.lineTo(p)
            
            if i+1 == n:
                # Done
                break
            
            # Get next point
            next = poly.at(i+1)
            
            # Make our paths
            last_path.lineTo(p)
            next_path = QPainterPath()
            next_path.moveTo(p)
            next_path.lineTo(next)
            
            # Get angle between the two components
            u, v = QVector2D(last-p), QVector2D(next-p)
            cos_theta = QVector2D.dotProduct(u.normalized(), v.normalized())
            
            # If the angle is large enough to need compensation
            if (cos_theta < cutoff and
                    last_path.length() > offset and
                    next_path.length() > offset):
                # Calculate the extended point
                t = last_path.percentAtLength(offset)
                c1 = p+(last_path.pointAtPercent(t)-last)
                c2 = p
                t = next_path.percentAtLength(offset)
                ep = next_path.pointAtPercent(t)
                if offset > 2:
                    # Can smooth it for larger offsets
                    path.cubicTo(c1, c2, ep)
                else:
                    # This works for small offsets < 0.5 mm 
                    path.lineTo(c1)
                    path.lineTo(ep)
            
            # Update last
            last_path = next_path
            last = p
        return path.toSubpathPolygons(IDENITY_MATRIX)
