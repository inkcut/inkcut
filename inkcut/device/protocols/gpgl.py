# -*- coding: utf-8 -*-
"""
Created on Jul 25, 2015

Thanks to Lex Wernars

@author: jrm
@author: lwernars
"""
import asyncio

from atom.api import Bool, Bytes, Float, Instance, Int, Str, Value
from inkcut.core.api import Model, log
from inkcut.device.plugin import DeviceProtocol

#: Ends each batch under flow control. FG asks for the machine's name,
#: which it answers once it reaches the query, after the commands before.
SENTINEL = "\x03FG\x03"

#: Asks for the machine's state, which it answers at once: 0 ready,
#: 1 busy, 2 ready without media, 3 paused.
STATE = "\x1b\x05"


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


class GPGLProtocol(DeviceProtocol):
    config = Instance(GPGLConfig, ()).tag(config=True)

    #: Bytes per batch, to fill one BLE write
    batch_size = Int(180)

    #: Batches left unanswered at most
    window = Int(8)

    #: Seconds the machine must sit idle with batches unanswered before
    #: they are taken as lost
    lost_after = Float(1.0)

    #: Seconds to wait for the answer to a state query
    reply_timeout = Float(1.0)

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
        await self.write('\x03!%i' % v)

    async def set_force(self, f):
        await self.write("\x03FX%i,1" % f)

    async def set_pen(self, p):
        pass

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
            elif self._unanswered:
                #: The answer to a batch's query
                self._unanswered -= 1
            self._heard.set()

    def status_received(self, data):
        self._paused = data.strip(b'\x03 ')[:1] == b'3'
        self._heard.set()
