"""
Copyright (c) 2022, Kārlis Seņko.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 22, 2022

@author: karliss
"""
from PyQt5.QtCore import QPointF
from enaml.qt.QtGui import QPainterPath
from atom.api import Int, Instance, Float
from inkcut.device.plugin import DeviceFilter, Model
from inkcut.core.utils import split_painter_path, join_painter_paths, path_element_to_point


class RepeatConfig(Model):
    steps = Int(1).tag(config=True)
    # measured in 1/90inch like most other inkcut distances
    closed_loop_distance = Float(0.1, strict=False).tag(config=True)

class RepeatFilter(DeviceFilter):
    config = Instance(RepeatConfig, ()).tag(config=True)

    def apply_to_model(self, model, job):
        if self.config.steps <= 1:
            return model

        parts = split_painter_path(model)
        max_gap_2 = self.config.closed_loop_distance * self.config.closed_loop_distance
        result = QPainterPath()
        for part in parts:
            gap = path_element_to_point(part.elementAt(0)) -\
                  path_element_to_point(part.elementAt(part.elementCount() - 1))
            length2 = QPointF.dotProduct(gap, gap)
            if length2 < max_gap_2:
                result.addPath(part)
                for i in range(1, self.config.steps):
                    result.connectPath(part)
            else:
                for i in range(self.config.steps):
                    result.addPath(part)
        return result