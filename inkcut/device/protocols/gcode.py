# -*- coding: utf-8 -*-
"""
Created on Dec 30, 2016

@author: jrm
"""
from inkcut.device.plugin import DeviceProtocol, Model
from enaml.qt.QtCore import QT_TRANSLATE_NOOP
from atom.api import (
    Bool, Float, Enum, Int, Instance, Str
)

class GCodeConfig(Model):
    use_builtin = Bool(True).tag(config=True)

    TOOL_LIFT_IMPLICIT = 0 # assume that device will lift/lower tool based on G00 / G01
    TOOL_LIFT_CUSTOM = 1 # user specified GCODE
    TOOL_LIFT_Z = 2 # move Z axis on 3 axis machine


    # QT_TRANSLATE_NOOP("protocols", "Implicit")
    tool_lift_modes = {
        TOOL_LIFT_IMPLICIT: QT_TRANSLATE_NOOP("protocols", "Implicit"),
        TOOL_LIFT_CUSTOM: QT_TRANSLATE_NOOP("protocols", "Custom"),
        TOOL_LIFT_Z: QT_TRANSLATE_NOOP("protocols", "Z"),
    }

    lift_mode = Enum(*tool_lift_modes.keys()).tag(config=True)
    precision = Int(0).tag(config=True)

    lower_z = Float(0).tag(config=True)
    upper_z = Float(1).tag(config=True)

    lift_gcode = Str().tag(config=True)
    lower_gcode = Str().tag(config=True)

class GCodeProtocol(DeviceProtocol):

    config = Instance(GCodeConfig, ()).tag(config=True)

    _currently_up = Bool()
    scale = 1 # Float(25.4/90)

    def send_command_block(self, commands):
        if commands:
            if not commands.endswith("\n"):
                self.write(commands + "\n")
            else:
                self.write(commands)

    def _lift(self):
        if self.config.lift_mode == GCodeConfig.TOOL_LIFT_CUSTOM:
            self.send_command_block(self.config.lift_gcode)

    def _lower(self):
        if self.config.lift_mode == GCodeConfig.TOOL_LIFT_CUSTOM:
            self.send_command_block(self.config.lower_gcode)

    def connection_made(self):
        if self.config.use_builtin:
            self.write("G28; Return to home\n")
            self.write("G98; Return to initial z\n")
            self.write("G90; Use absolute coordinates\n")
    
    def move(self, x, y, z, absolute=True):
        if self._currently_up != (z == 0):
            if self._currently_up:
                self._lower()
            else:
                self._lift()
            if z == 0:
                self._currently_up = True
            else:
                self._currently_up = False
        x, y = x * self.scale, y * self.scale
        line = "G0{:d} X{:.{precision}f} Y{:.{precision}f}".format(z, x, y, precision=self.config.precision)
        if self.config.lift_mode == GCodeConfig.TOOL_LIFT_Z:
            physical_z = self.config.lower_z if z == 1 else self.config.upper_z
            line += " Z{:.{precision}f}".format(physical_z, precision=self.config.precision)
        line += "\n"
        self.write(line)

    def set_force(self, f):
        raise NotImplementedError
        
    def set_velocity(self, v):
        raise NotImplementedError
        
    def set_pen(self, p):
        raise NotImplementedError

    def finish(self):
        if self.config.use_builtin:
            self.write("G28; Return to home\n")
            self.write("G98; Return to initial z\n")

    def connection_lost(self):
        pass