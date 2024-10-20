# -*- coding: utf-8 -*-
"""
Created on Dec 30, 2016

@author: jrm
"""
import atom.api
import twisted.internet.task

from inkcut.core.utils import async_sleep
from inkcut.device.plugin import DeviceProtocol, Model
from twisted.internet import defer
from enaml.qt.QtCore import QT_TRANSLATE_NOOP
from atom.api import Bool, Float, Enum, Int, Instance, Str, Bytes


class GCodeConfig(Model):
    use_builtin = Bool(True).tag(config=True)

    TOOL_LIFT_IMPLICIT = 0  # assume that device will lift/lower tool based on G00 / G01
    TOOL_LIFT_CUSTOM = 1  # user specified GCODE
    TOOL_LIFT_Z = 2  # move Z axis on 3 axis machine

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

    GCODE_STREAM_NONE = 0  # no additional gcode streaming protocol at this level
    GCODE_STREAM_OK = 1  # Basic streaming mode: wait for OK after each command.
    # Used by GRBL Marlin and other 3d printer firmware.

    GCODE_STREAM_MODES = {
        GCODE_STREAM_NONE: QT_TRANSLATE_NOOP("gcode", "None"),
        GCODE_STREAM_OK: QT_TRANSLATE_NOOP("gcode", "OK"),
    }

    stream_mode = Enum(*GCODE_STREAM_MODES.keys()).tag(config=True)


class GCodeProtocol(DeviceProtocol):

    config = Instance(GCodeConfig, ()).tag(config=True)

    _currently_up = Bool()
    scale = 1  # Float(25.4/90)
    _ok_waiting = Int(default=0)
    _receive_buffer = Bytes()
    _reactor = atom.api.Value()

    def _default_reactor(self):
        from twisted.internet import reactor as reactor

        return reactor

    def non_interactive_streaming(self):
        return (
            self.config.stream_mode == GCodeConfig.GCODE_STREAM_NONE
            or self.transport.always_spools
        )

    @defer.inlineCallbacks
    def write(self, commands):
        if commands:
            stream_mode = self.config.stream_mode
            if self.non_interactive_streaming():
                yield self._send_commands_plain(commands)
            elif stream_mode == GCodeConfig.GCODE_STREAM_OK:
                yield defer.maybeDeferred(self._send_stream_simple_ok, commands)
            else:
                logging.debug("Unexpected streaming mode")

    @defer.inlineCallbacks
    def send_command_block(self, commands):
        yield self.write(commands)

    def _split_gcode(self, commands: str):
        result = []
        for line in commands.split("\n"):
            line = line.strip()
            if not line or line.find(";") == 0:
                continue
            result.append(line)
        return result

    @defer.inlineCallbacks
    def _send_commands_plain(self, commands):
        if commands:
            if not commands.endswith("\n"):
                commands += "\n"
            if self.transport is not None:
                yield self.transport.write(commands)

    @defer.inlineCallbacks
    def _send_stream_simple_ok(self, data):
        for line in self._split_gcode(data):
            while self._ok_waiting > 0:
                yield twisted.internet.task.deferLater(self._reactor, 0.001)
                # yield async_sleep(1) #TODO look into better solution provided by twisted
            if self.transport is not None:
                self._ok_waiting += 1
                yield self.transport.write(line + "\n")
            while self._ok_waiting > 0:
                yield twisted.internet.task.deferLater(self._reactor, 0.001)
                # yield async_sleep(1) #TODO look into better solution provided by twisted

    def data_received(self, data: bytes):
        super().data_received(data)
        if self.non_interactive_streaming():
            return
        self._receive_buffer += data
        buff: bytes = self._receive_buffer
        if buff.find(b"\n") >= 0:
            ends_with_newline = buff.endswith(b"\n")
            parts = buff.split(b"\n")
            self._receive_buffer = bytes()
            if ends_with_newline:
                for line in parts:
                    self.line_received(line.decode())
            elif len(parts) > 0:
                self._receive_buffer = parts[-1]
                for line in parts[:-1]:
                    self.line_received(line.decode())

    def line_received(self, line):
        if line.startswith("ok"):
            self._ok_waiting -= 1

    @defer.inlineCallbacks
    def _lift(self):
        if self.config.lift_mode == GCodeConfig.TOOL_LIFT_CUSTOM:
            yield self.send_command_block(self.config.lift_gcode)

    @defer.inlineCallbacks
    def _lower(self):
        if self.config.lift_mode == GCodeConfig.TOOL_LIFT_CUSTOM:
            yield self.send_command_block(self.config.lower_gcode)

    @defer.inlineCallbacks
    def connection_made(self):
        self._ok_waiting = 0
        if self.config.use_builtin:
            yield self.write(
                "G28; Return to home\n"
                + "G98; Return to initial z\n"
                + "G90; Use absolute coordinates\n"
            )

    @defer.inlineCallbacks
    def move(self, x, y, z, absolute=True):
        if self._currently_up != (z == 0):
            if self._currently_up:
                yield self._lower()
            else:
                yield self._lift()
            if z == 0:
                self._currently_up = True
            else:
                self._currently_up = False
        x, y = x * self.scale, y * self.scale
        line = "G0{:d} X{:.{precision}f} Y{:.{precision}f}".format(
            z, x, y, precision=self.config.precision
        )
        if self.config.lift_mode == GCodeConfig.TOOL_LIFT_Z:
            physical_z = self.config.lower_z if z == 1 else self.config.upper_z
            line += " Z{:.{precision}f}".format(
                physical_z, precision=self.config.precision
            )
        line += "\n"
        yield self.write(line)

    def set_force(self, f):
        raise NotImplementedError

    def set_velocity(self, v):
        raise NotImplementedError

    def set_pen(self, p):
        raise NotImplementedError

    @defer.inlineCallbacks
    def finish(self):
        if self.config.use_builtin:
            yield self.write("G28; Return to home\n")
            yield self.write("G98; Return to initial z\n")

    def connection_lost(self):
        pass
