"""
Copyright (c) 2018, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 14, 2018

@author: jrm
"""
from atom.api import Float, Enum, Instance
from inkcut.device.plugin import DeviceFilter, Model
from inkcut.core.utils import unit_conversions
from enaml.qt.QtGui import QPainterPath


class OvercutConfig(Model):
    #: Overcut in user units
    overcut = Float(strict=False).tag(config=True)
    
    #: Units for display 
    overcut_units = Enum(*unit_conversions.keys()).tag(config=True)
    
    def _default_overcut_units(self):
        return 'mm'


class OvercutFilter(DeviceFilter):
    #: Change config
    config = Instance(OvercutConfig, ()).tag(config=True)
    
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
        d = self.config.overcut
        if d <= 0:
            return polypath
        
        result = []
        for poly in polypath:
            if poly.isClosed():
                self.apply_overcut(poly, d)
            result.append(poly)
        
        return result
    
    def apply_overcut(self, poly, overcut):
        """ Apply overcut to the given polygon by going "past" by overcut
        distance.
        
        """
        # Use a QPainterPath to track the distance in c++
        path = QPainterPath()
        for i, p in enumerate(poly):
            if i == 0:
                path.moveTo(p)
                continue  # Don't add a double point
            
            path.lineTo(p)
            
            # Check if that point is past the distance we need to go
            if path.length() > overcut: 
                t = path.percentAtLength(overcut)
                poly.append(path.pointAtPercent(t))
                return  # Done!
            else:
                # Add the point and go to the next
                poly.append(p)
