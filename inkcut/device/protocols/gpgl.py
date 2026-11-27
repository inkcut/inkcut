# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

Thanks to Lex Wernars

@author: jrm
@author: lwernars
"""
import asyncio

from atom.api import Bool, Bytes, Float, Instance, Int, List, Str, Value
from inkcut.core.api import Model, log
from inkcut.device.plugin import DeviceProtocol

#: Ends each batch under flow control. FG asks for the machine's name,
#: which it answers once it reaches the query, after the commands before.
SENTINEL = "\x03FG\x03"

#: Asks for the machine's state, which it answers at once: 0 ready,
#: 1 busy, 2 ready without media, 3 paused.
STATE = "\x1b\x05"

#: Asks which tool is in each holder (Cameo 4 and later)
TOOLS = "\x1b\x15"

#: Tool codes a Cameo 4 reports for each holder
TOOL_EMPTY = 0
TOOL_AUTOBLADE = 2
TOOL_NAMES = {
    0: 'Empty',
    1: 'Ratchet blade',
    2: 'AutoBlade',
    3: 'Deep-cut blade',
    4: 'Kraft blade',
    5: 'Rotary blade',
    7: 'Pen',
    255: 'Error',
}


def to_machine_units(value, per_unit, highest):
    """ Round value to the nearest whole machine unit, from 1 to highest
    (no upper limit if highest is 0).

    """
    units = int(value / per_unit + 0.5)
    return max(1, min(highest or units, units))


class GPGLConfig(Model):
    #: Terminate each command with ETX (0x03). Machines like the Cameo 4
    #: do not run a command until it is terminated.
    append_etx = Bool().tag(config=True)

    #: Send jobs in batches, each ending with a query the machine answers
    #: once it gets there, and keep only a few unanswered. This keeps the
    #: machine's buffer fed without overfilling it, where one write per
    #: command is too slow (over BLE each write takes ~60 ms whatever its
    #: size). Nothing is sent while the machine is paused, since it
    #: discards what arrives then. Needs a machine that answers queries.
    flow_control = Bool().tag(config=True)

    #: Set the AutoBlade in tool holder 1 to autoblade_depth before each
    #: job. The machine taps the blade against a post to turn it.
    autoblade = Bool().tag(config=True)

    #: AutoBlade depth, 0-10 as on the blade's scale
    autoblade_depth = Int(3).tag(config=True)

    #: Machine force unit in grams, and the highest unit. Inkcut's force
    #: is in grams; GPGL machines take their own scale, which differs
    #: between them, so drivers set these. 0 sends force unconverted.
    force_grams_per_unit = Float().tag(config=True)
    force_max = Int().tag(config=True)

    #: Machine speed unit in mm/s, and the highest unit. Inkcut's speed is
    #: in in/s, the only unit its settings offer. 0 sends it unconverted.
    speed_mm_s_per_unit = Float().tag(config=True)
    speed_max = Int().tag(config=True)


class GPGLProtocol(DeviceProtocol):
    config = Instance(GPGLConfig, ()).tag(config=True)

    #: Bytes per batch, to fill one BLE write
    batch_size = Int(180)

    #: Batches left unanswered at most
    window = Int(8)

    #: Seconds the machine must sit idle with batches unanswered before
    #: they are taken as lost
    lost_after = Float(1.0)

    #: Seconds to wait for the machine to answer a query
    reply_timeout = Float(2.0)

    #: Tool code per holder from the last get_tools, empty if unknown
    tools = List()

    #: Whether writes are batched, which is only during a job: jogging
    #: sends each move at once
    _batching = Bool()

    #: Commands for the next batch
    _batch = Str()

    #: Batches sent whose query is unanswered
    _unanswered = Int()

    #: Whether the machine last reported itself paused
    _paused = Bool()

    #: Replies collected up to their ETX
    _replies = Bytes()

    #: Future for the answer to a state query
    _state = Value()

    #: Future for the answer to any other query
    _reply = Value()

    #: Set whenever the machine replies or reports its state
    _heard = Instance(asyncio.Event, ())

    def controls_flow(self):
        transport = self.transport
        return self.config.flow_control and not (
            transport is not None and transport.always_spools)

    async def write(self, data):
        if self.config.append_etx:
            data += "\x03"
        if not self._batching:
            return await super().write(data)
        if len(self._batch) + len(data) + len(SENTINEL) > self.batch_size:
            await self._send_batch()
        self._batch += data

    async def init(self):
        self._batching = False
        self._batch = ''
        await self.write("\x03\x03H")

    async def start_job(self):
        if self.config.autoblade:
            await self.set_autoblade_depth(self.config.autoblade_depth)
        self._batching = self.controls_flow()
        self._unanswered = 0

    async def finish(self):
        if not self._batching:
            return
        if self._batch:
            await self._send_batch()
        #: Disconnecting clears what the machine has yet to run, so wait
        #: until it has run everything
        await self._wait(0)
        self._batching = False

    async def move(self, x, y, z, absolute=True):
        await self.write("\x03%s%i,%i"%('D' if z else 'M', x, y))

    async def set_velocity(self, v):
        await self.write('\x03!%i' % self.machine_speed(v))

    async def set_force(self, f):
        await self.write("\x03FX%i,1" % self.machine_force(f))

    def machine_force(self, grams):
        """ Force as sent: in machine units if the driver gave a scale. """
        c = self.config
        if not c.force_grams_per_unit:
            return grams
        return to_machine_units(grams, c.force_grams_per_unit, c.force_max)

    def machine_speed(self, in_s):
        """ Speed as sent: in machine units if the driver gave a scale. """
        c = self.config
        if not c.speed_mm_s_per_unit:
            return in_s
        return to_machine_units(in_s * 25.4, c.speed_mm_s_per_unit, c.speed_max)

    async def set_pen(self, p):
        pass

    async def set_autoblade_depth(self, depth):
        """ Select tool holder 1 and turn its AutoBlade to depth. Skipped
        if the machine reports a different tool there; machines that do
        not answer get the commands anyway.

        """
        tools = await self.get_tools()
        if tools and tools[0] not in (TOOL_AUTOBLADE, TOOL_EMPTY):
            log.warning("gpgl | AutoBlade depth not set, tool holder 1 "
                        "has tool {}".format(tools[0]))
            return
        depth = max(0, min(10, depth))
        log.debug("gpgl | AutoBlade depth {}".format(depth))
        await self.write("\x03J1")
        await self.write("\x03TF%i,1" % depth)

    async def get_tools(self):
        """ Ask which tool is in each holder (Cameo 4 and later).

        Returns
        -------
        tools: list or None
            Tool code per holder, or None if the machine did not answer.

        """
        reply = await self.query(TOOLS)
        tools = None
        if reply is not None:
            try:
                tools = [int(t) for t in reply.decode().split(',')]
            except ValueError:
                log.warning("gpgl | unexpected tool reply {}".format(reply))
        self.tools = tools or []
        return tools

    async def query(self, cmd):
        """ Send a query and return the machine's reply without its ETX,
        or None if no reply comes within reply_timeout.

        Not for use while batches are unanswered, whose answers would be
        taken as the reply.

        """
        self._reply = asyncio.get_running_loop().create_future()
        try:
            await super().write(cmd)
            return await asyncio.wait_for(self._reply, self.reply_timeout)
        except asyncio.TimeoutError:
            log.debug("gpgl | no reply to {!r}".format(cmd))
            return None
        finally:
            self._reply = None

    async def get_state(self):
        """ Ask the machine's state.

        Returns
        -------
        state: str or None
            '0' ready, '1' busy, '2' ready without media, '3' paused, or
            None if the machine did not answer.

        """
        self._state = asyncio.get_running_loop().create_future()
        try:
            await super().write(STATE)
            return await asyncio.wait_for(self._state, self.reply_timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self._state = None

    async def _send_batch(self):
        await self._wait(self.window - 1)
        batch, self._batch = self._batch, ''
        await super().write(batch + SENTINEL)
        self._unanswered += 1

    async def _wait(self, most):
        """ Wait until at most `most` batches are unanswered and the
        machine is not paused.

        Batches still unanswered after the machine has sat idle for
        lost_after seconds were lost, sent just as it paused, and are no
        longer waited on.

        """
        loop = asyncio.get_running_loop()
        idle = None
        while True:
            state = await self.get_state()
            if state == '3' or self._paused:
                idle = None
            elif self._unanswered <= most:
                return
            elif state in ('0', '2'):
                if idle is None:
                    idle = loop.time()
                elif loop.time() - idle >= self.lost_after:
                    log.warning("gpgl | {} batch(es) never answered, likely "
                                "sent as the machine paused".format(
                                    self._unanswered))
                    self._unanswered = 0
                    return
            else:
                idle = None
            self._heard.clear()
            try:
                await asyncio.wait_for(self._heard.wait(), 0.2)
            except asyncio.TimeoutError:
                pass

    def data_received(self, data):
        self._replies += data
        while b'\x03' in self._replies:
            reply, self._replies = self._replies.split(b'\x03', 1)
            reply = reply.strip()
            if len(reply) == 1:
                #: A state
                if self._state is not None and not self._state.done():
                    self._state.set_result(reply.decode())
            elif self._reply is not None and not self._reply.done():
                self._reply.set_result(reply)
            elif self._unanswered:
                #: The answer to a batch's query
                self._unanswered -= 1
            self._heard.set()

    def status_received(self, data):
        self._paused = data.strip(b'\x03 ')[:1] == b'3'
        self._heard.set()
