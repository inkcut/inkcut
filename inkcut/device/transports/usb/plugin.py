# -*- coding: utf-8 -*-
"""
Native libusb (pyusb) transport.

Talks directly to USB printer-class cutters that macOS exposes no
serial port or raw CUPS queue for, e.g. the Anhui Anyu family
(Vevor/ANAgraph rebrands, 0483:5750 "CH554_CDC"). That firmware
presents printer-class descriptors but actually implements CDC
control requests: it buffers data without cutting until the line
coding is set and DTR/RTS are asserted, and it crashes its USB stack
when macOS suspends the idle port. The transport therefore performs
the CDC handshake on connect and re-asserts DTR/RTS from a keepalive
thread while connected.

Created on Aug 17, 2026
"""
import struct
import threading
import time
from collections import deque, namedtuple

from twisted.internet.defer import Deferred

from inkcut.core.utils import defer_to_thread

from atom.api import Bool, Instance, Int, Str, Value

from inkcut.core.api import Model, log
from inkcut.device.plugin import DeviceTransport

try:
    import usb.core
    import usb.util
    PYUSB_AVAILABLE = True
except ImportError as e:
    log.warning("usb | pyusb not available: {}".format(e))
    PYUSB_AVAILABLE = False


#: Seconds between DTR/RTS keepalive assertions
KEEPALIVE_S = 15

#: Per-attempt bulk write timeout (ms). A timeout is NOT fatal: pyusb
#: (1.3.1, libusb1 backend) returns a short count when a timed-out
#: transfer moved bytes and only raises USBTimeoutError when nothing was
#: transferred, so a timeout means "buffer full, zero bytes consumed"
#: and the same offset is retried as flow control.
WRITE_TIMEOUT_MS = 1000

#: Abort only when NOTHING has been accepted for this long (s). A full
#: CH554 ring buffer NAKs the endpoint while the cutter chews through
#: queued moves — on a large job that back-pressure can legitimately
#: hold single writes for minutes in total, but zero progress for this
#: long means the firmware is wedged or the panel is offline/in origin
#: mode.
NO_PROGRESS_ABORT_S = 90.0

#: Soft cap on bytes queued to the writer thread. Pacing in the submit
#: loop should keep the queue tiny; crossing this only logs a warning
#: (data is never dropped and the caller is never blocked).
WRITER_QUEUE_MAX = 512 * 1024

#: User-facing error when the job is aborted mid-transfer
STALLED_MSG = ("Cutter stalled mid-transfer; job aborted to avoid "
               "duplicate cuts. Power-cycle the cutter and resend the "
               "job.")

#: Settle time after a USB port reset before the device re-enumerates (s)
RESET_SETTLE_S = 2.0

#: How long to poll for the device to reappear after a reset/drop (s)
RECLAIM_WAIT_S = 10.0

#: flush() result when the wait was abandoned because the job was
#: cancelled: the caller drops the queue instead of draining it
FLUSH_CANCELLED_MSG = "flush cancelled"

#: User-facing error when the bulk pipe cannot be made to flow
WEDGED_PIPE_MSG = ("The cutter is not accepting data (wedged USB pipe). "
                   "Power-cycle the cutter and try again.")

#: Immutable snapshot of the config values the connect worker needs, so
#: the worker thread never reads live Atom members that the UI can edit
#: concurrently
UsbParams = namedtuple('UsbParams', 'vid pid endpoint cdc_init baud chunk_size')


def cdc_line_coding(baud):
    """ CDC SET_LINE_CODING payload: 1 stop bit, no parity, 8 data bits """
    return struct.pack('<IBBB', baud, 0, 0, 8)


class UsbConfig(Model):
    #: USB vendor id
    vid = Int(0x0483).tag(config=True)

    #: USB product id
    pid = Int(0x5750).tag(config=True)

    #: Bulk OUT endpoint address
    endpoint = Int(0x02).tag(config=True)

    #: Perform the CDC line-coding + DTR/RTS handshake on connect and
    #: keep re-asserting DTR/RTS while connected
    cdc_init = Bool(True).tag(config=True)

    #: Baud rate for the CDC line coding (some firmwares expect 38400)
    baud = Int(9600).tag(config=True)

    #: Max bytes per bulk transfer. The CH554 endpoint max packet is 64
    #: bytes and its firmware wedges when its tiny buffer fills; some
    #: community senders use 16 for extra safety.
    chunk_size = Int(64).tag(config=True)


class UsbTransport(DeviceTransport):

    #: Default config
    config = Instance(UsbConfig, ()).tag(config=True)

    #: The pyusb device handle
    _dev = Value()

    #: Frozen copy of the config the workers run against. Set on the
    #: reactor thread by connect(); read by the writer and keepalive
    #: threads so a config edit mid-job cannot change them under way.
    _params = Value()

    #: Serializes all USB access between writes and the keepalive thread
    _lock = Value(factory=threading.Lock)

    #: Signals the keepalive thread to exit
    _stop = Value()

    #: The active keepalive thread (at most one per transport instance)
    _keepalive_thread = Value()

    #: True while a connect attempt is in flight on the worker thread.
    #: Only touched on the reactor thread, so a plain flag suffices.
    _connecting = Bool()

    #: Connect-attempt generation. Written only on the reactor thread:
    #: disconnect() bumps it to cancel an in-flight connect, whose
    #: callbacks then refuse to complete (see connect()). The worker
    #: reads it to bail out of long recovery polls early.
    _generation = Int()

    #: FIFO of pending write() payloads, drained in order by the writer
    #: thread. Guarded by _writer_cond (never by _lock).
    _writer_queue = Value(factory=deque)

    #: Guards _writer_queue/_writer_size and wakes the writer thread
    _writer_cond = Value(factory=threading.Condition)

    #: Bytes currently queued (for the WRITER_QUEUE_MAX warning)
    _writer_size = Int()

    #: The WRITER_QUEUE_MAX warning fired for this session
    _writer_warned = Bool()

    #: The active writer thread (at most one per transport instance)
    _writer_thread = Value()

    #: True while the writer thread is pushing a popped payload to the
    #: device. Guarded by _writer_cond: flush() is done only when the
    #: queue is empty AND no payload is in flight.
    _writer_active = Bool()

    #: User-facing message from the last fatal write/abort error, so the
    #: device layer can show something better than "connection error".
    #: Written on the main thread only.
    last_error = Str()

    #: The exception that killed the writer thread, published under
    #: _writer_cond BEFORE _writer_active is cleared: flush() must see
    #: the failure in the same critical section that makes the writer
    #: look idle, or a failed final payload gets flushed as success
    #: (mark_dead lands on the main thread later). Cleared on connect.
    _writer_error = Value()

    #: Test hook (plain class attribute, not an Atom member): when True,
    #: write() runs the drain logic inline on the calling thread and no
    #: writer thread is started, restoring fully synchronous semantics
    #: for deterministic tests and offline/cli use.
    _writer_inline = False

    # -------------------------------------------------------------------------
    # Device handling
    # -------------------------------------------------------------------------
    def _cdc_init(self, dev, config=None):
        config = config or self.config
        if not config.cdc_init:
            return
        dev.ctrl_transfer(0x21, 0x20, 0, 0, cdc_line_coding(config.baud),
                          timeout=2000)
        dev.ctrl_transfer(0x21, 0x22, 0x03, 0, None, timeout=2000)

    def _claim(self, config=None):
        """ Find, claim, and init the device. Must hold the lock. The
        connect worker passes its UsbParams snapshot as `config`; the
        write path (reactor thread) omits it and reads the live config.
        """
        config = config or self.config
        dev = usb.core.find(idVendor=config.vid, idProduct=config.pid)
        if dev is None:
            raise IOError("USB device %04x:%04x not found"
                          % (config.vid, config.pid))
        try:
            usb.util.claim_interface(dev, 0)
            self._cdc_init(dev, config)
        except Exception:
            #: Don't leak a half-claimed handle when init fails
            try:
                usb.util.dispose_resources(dev)
            except Exception:
                pass
            raise
        self._dev = dev
        return dev

    def _release(self, reset=False):
        """ Drop the device handle. Must hold the lock. """
        dev = self._dev
        self._dev = None
        if dev is None:
            return
        if reset:
            try:
                dev.reset()
                log.debug("usb | reset issued")
            except usb.core.USBError as e:
                log.warning("usb | reset failed: {}".format(e))
        try:
            usb.util.dispose_resources(dev)
        except Exception:
            pass

    def _recover(self, reset, deadline=None, config=None, cancelled=None):
        """ Drop the handle (optionally resetting the port), wait for the
        device to re-enumerate, and reclaim + re-init it. Must hold the
        lock. A reset detaches the CH554 from the bus for 0.5-2s, so the
        claim is polled rather than attempted once. `cancelled` (from the
        connect worker) aborts the poll early when disconnect() cancels
        the attempt.
        """
        self._release(reset=reset)
        if reset:
            time.sleep(RESET_SETTLE_S)
        end = time.monotonic() + RECLAIM_WAIT_S
        if deadline is not None:
            end = min(end, deadline)
        while True:
            if cancelled is not None and cancelled():
                raise IOError("USB connect cancelled")
            try:
                return self._claim(config)
            except (IOError, usb.core.USBError) as e:
                if time.monotonic() >= end:
                    raise
                time.sleep(0.5)

    def _stop_keepalive(self):
        """ Stop the session workers (keepalive AND writer: they share
        the stop event) and drop anything not yet sent — after a
        disconnect/abort nothing queued may reach the cutter. Safe to
        call while holding _lock (the join skips the current thread, so
        a writer aborting itself cannot deadlock here).
        """
        stop = self._stop
        if stop is not None:
            stop.set()
        self._stop = None
        self._keepalive_thread = None
        with self._writer_cond:
            self._writer_queue.clear()
            self._writer_size = 0
            self._writer_cond.notify_all()
        wt = self._writer_thread
        if wt is not None and wt is not threading.current_thread():
            wt.join(timeout=1.5)
            if not wt.is_alive():
                self._writer_thread = None
            #: else: the join timed out (writer inside a reset settle or
            #: a blocked bulk attempt) — keep the ref so ownership
            #: checks still see the live thread; a later
            #: connect()/disconnect() reaps it once it has exited
        #: A writer thread stopping itself leaves its (dead) ref behind;
        #: the next connect()/disconnect() reaps it. Meanwhile write()
        #: enqueues into the void, which is correct: the session is dead
        #: and connected goes False on the main thread right after.

    def _keepalive(self, stop):
        """ Re-assert DTR/RTS periodically so macOS never suspends the
        port (the CH554 firmware crashes on suspend). Never blocks on the
        lock: a busy lock means a write is in flight, which is already
        suspend-preventing traffic. On failure the handle is only marked
        dead; recovery belongs to the write path.
        """
        while not stop.wait(KEEPALIVE_S):
            if not self._lock.acquire(blocking=False):
                continue
            try:
                dev = self._dev
                p = self._params
                cdc_init = (p.cdc_init if p is not None
                            else self.config.cdc_init)
                if dev is None or not cdc_init:
                    continue
                try:
                    dev.ctrl_transfer(0x21, 0x22, 0x03, 0, None, timeout=2000)
                except usb.core.USBError as e:
                    log.warning("usb | keepalive failed: {}".format(e))
                    self._release()
            finally:
                self._lock.release()

    # -------------------------------------------------------------------------
    # Transport API
    # -------------------------------------------------------------------------
    def connect(self):
        """ Run the blocking claim/recovery/probe sequence on a worker
        thread and return a Deferred, so reset settles, reclaim polling
        and pipe probes (worst case tens of seconds with a wedged or
        unplugged cutter) never block the reactor/GUI thread. The Atom
        model and the protocol are only touched from the reactor thread,
        in the callbacks.
        """
        if not PYUSB_AVAILABLE:
            raise EnvironmentError("pyusb is not installed")
        if self._connecting:
            raise IOError("A USB connect attempt is already in progress")
        self._connecting = True
        # Reap any keepalive thread left over from a previous session
        self._stop_keepalive()
        #: Snapshot everything the worker needs on the reactor thread —
        #: the worker must not read live Atom config the UI can edit
        c = self.config
        params = UsbParams(c.vid, c.pid, c.endpoint, c.cdc_init, c.baud,
                           c.chunk_size)
        self._params = params
        #: disconnect() bumps _generation to cancel this attempt; the
        #: callbacks below then refuse to complete and instead clean up
        gen = self._generation
        d = defer_to_thread(self._connect_blocking, gen, params)

        def on_connected(result):
            if self._generation != gen:
                # disconnect() cancelled this attempt while the worker
                # ran: the claimed handle must not survive. The worker is
                # done, so the lock is uncontended here.
                log.debug("usb | connect cancelled; releasing handle")
                with self._lock:
                    self._release()
                return
            log.debug("usb | {:04x}:{:04x} connected".format(
                params.vid, params.pid))
            self.connected = True
            stop = threading.Event()
            self._stop = stop
            t = threading.Thread(target=self._keepalive, args=(stop,))
            t.daemon = True
            self._keepalive_thread = t
            t.start()
            self._writer_warned = False
            self._writer_active = False
            self._writer_error = None
            self.last_error = ''
            if not self._writer_inline:
                wt = threading.Thread(target=self._writer, args=(stop,),
                                      name='inkcut-usb-writer')
                wt.daemon = True
                self._writer_thread = wt
                wt.start()
            self.protocol.connection_made()

        def on_failed(failure):
            self.connected = False
            if self._generation != gen:
                # Failure paths release the handle themselves; after a
                # deliberate disconnect the error is not worth a dialog
                log.debug("usb | cancelled connect failed: {}".format(
                    failure.value))
                return
            return failure

        d.addCallbacks(on_connected, on_failed)

        def clear_connecting(result):
            self._connecting = False
            return result

        d.addBoth(clear_connecting)
        return d

    def _connect_blocking(self, gen, config):
        """ Claim, self-heal, and probe the device. Runs on a worker
        thread with `config` a frozen UsbParams snapshot: the only Atom
        state it touches is `_dev` (guarded by the lock, like the write
        path); model flags and the protocol are reactor-thread-only, in
        the callbacks. Holds the lock for the whole sequence so nothing
        can release the handle between the claim and the probe.
        """
        def cancelled():
            return self._generation != gen
        with self._lock:
            try:
                self._claim(config)
            except (IOError, usb.core.USBError) as e:
                # The CH554 crashes its USB stack when the port suspends
                # between jobs (no keepalive runs while disconnected). A
                # port reset usually revives it — try that before failing
                # so a job start is self-healing instead of requiring a
                # physical power-cycle.
                log.warning("usb | claim failed ({}), trying reset "
                            "recovery".format(e))
                #: No handle was kept on failure, so reset via a fresh
                #: find before polling the reclaim
                dev = usb.core.find(idVendor=config.vid,
                                    idProduct=config.pid)
                if dev is not None:
                    try:
                        dev.reset()
                        log.debug("usb | reset issued on connect")
                    except usb.core.USBError as re:
                        log.warning("usb | reset failed: {}".format(re))
                    finally:
                        try:
                            usb.util.dispose_resources(dev)
                        except Exception:
                            pass
                    time.sleep(RESET_SETTLE_S)
                try:
                    self._recover(reset=False, config=config,
                                  cancelled=cancelled)
                except (IOError, usb.core.USBError):
                    raise IOError(
                        "Could not connect to the cutter (USB %04x:%04x). "
                        "Power-cycle the cutter and try again."
                        % (config.vid, config.pid))
            # Verify the bulk pipe actually flows before the job starts:
            # the CH554 can be claimed and CDC-init'ed yet still have a
            # wedged bulk endpoint (deep idle-crash). A single space is a
            # DMPL/HPGL no-op; if it stalls we reset and retry once, so
            # the failure is caught here — with nothing cut — instead of
            # mid-job.
            for attempt in (1, 2):
                if cancelled():
                    self._release()
                    raise IOError("USB connect cancelled")
                try:
                    n = self._dev.write(config.endpoint, b' ', timeout=1500)
                    # A 0/None count means the byte never left the host:
                    # the pipe is not flowing even though write "worked"
                    if n != 1:
                        raise usb.core.USBError(
                            "pipe probe transferred %r bytes "
                            "(expected 1)" % (n,))
                    break
                except usb.core.USBError as e:
                    log.warning("usb | pipe probe failed ({}), "
                                "attempt {}".format(e, attempt))
                    if attempt == 2:
                        self._release(reset=True)
                        raise IOError(WEDGED_PIPE_MSG)
                    try:
                        self._recover(reset=True, config=config,
                                      cancelled=cancelled)
                    except (IOError, usb.core.USBError) as e2:
                        # Recovery itself failing is the same user-facing
                        # situation; don't leak the raw USB error
                        log.warning("usb | probe recovery failed: "
                                    "{}".format(e2))
                        raise IOError(WEDGED_PIPE_MSG)

    def _abort_job(self, reason):
        """ Abort the current job without resending anything: reset the
        port (revives the wedged CH554) but drop the claim entirely so no
        claimed-but-unprotected handle survives — Inkcut skips disconnect()
        once connected is False. Acquires the lock itself (callers hold
        it only around individual attempts). The caller marks the
        transport dead on the appropriate thread.
        """
        log.error("usb | %s; aborting job" % reason)
        with self._lock:
            self._release(reset=True)
        self._stop_keepalive()
        raise IOError(STALLED_MSG)

    def _fail(self, exc):
        """ Give up on this write: drop the handle, stop the workers and
        re-raise; the caller (inline write() or the writer thread) marks
        the transport dead on the appropriate thread. Must hold the lock.
        """
        self._release()
        self._stop_keepalive()
        raise exc

    def _call_on_main(self, fn):
        """ Run fn on the GUI thread when an enaml Application exists
        (Atom state and the protocol are main-thread-only there);
        inline otherwise (cli/tests — same convention as
        inkcut.core.utils.defer_to_thread). """
        from enaml.application import Application, deferred_call
        if Application.instance() is None:
            fn()
        else:
            deferred_call(fn)

    def write(self, data):
        """ Queue data for the writer thread and return immediately, so
        buffer back-pressure from the cutter never blocks the GUI. Falls
        back to the old synchronous behavior when _writer_inline is set
        (tests) or no writer thread exists (offline/cli use without
        connect()).
        """
        if hasattr(data, 'encode'):
            data = data.encode()
        log.debug("usb -> {}".format(data))
        self.last_write = data
        if self._writer_inline or self._writer_thread is None:
            try:
                self._drain_payload(data)
            except Exception as e:
                self.last_error = str(e)
                self.connected = False
                raise
            return
        with self._writer_cond:
            self._writer_size += len(data)
            if (self._writer_size > WRITER_QUEUE_MAX
                    and not self._writer_warned):
                self._writer_warned = True
                log.warning(
                    "usb | writer queue exceeds %d KB — host pacing is "
                    "not throttling; queueing anyway"
                    % (WRITER_QUEUE_MAX // 1024))
            self._writer_queue.append(data)
            self._writer_cond.notify()

    def flush(self, cancelled=None):
        """ Wait until everything queued has been handed to the device
        (queue empty and no payload mid-drain in the writer thread).

        With an enaml Application this returns a Deferred resolved by
        non-blocking timed_call polling on the main thread, or errbacked
        with the transport's last_error if the session dies while
        draining — the device layer awaits this before declaring a job
        complete, because disconnect() drops anything still queued.
        A writer failure is checked in the same critical section as the
        idle test: connected may still read True while mark_dead is in
        flight on the main thread, and that window must never flush a
        failed job as success.

        `cancelled` is an optional callable; once it returns True the
        wait stops with IOError(FLUSH_CANCELLED_MSG) so the caller can
        drop the rest instead of draining it to the cutter.

        Without an Application but with a live writer thread (cli/tests)
        this blocks on the writer's condition variable (a real wait, not
        a busy spin) until drained, cancelled or dead. In inline mode
        every write() already completed synchronously, so there is
        nothing to wait for.
        """
        if self._writer_inline or self._writer_thread is None:
            return
        from enaml.application import Application, timed_call
        cond = self._writer_cond

        def idle():
            #: caller must hold cond
            return not self._writer_queue and not self._writer_active

        if Application.instance() is None:
            with cond:
                while True:
                    err = self._writer_error
                    if err is not None or not self.connected:
                        raise IOError(self.last_error or str(err)
                                      or "connection error")
                    if cancelled is not None and cancelled():
                        raise IOError(FLUSH_CANCELLED_MSG)
                    if idle():
                        return
                    cond.wait(0.5)

        d = Deferred()

        def poll():
            #: the error check and the idle test share the cond so a
            #: failed final payload can never be observed as "done"
            with cond:
                err = self._writer_error
                done = idle()
            if err is not None or not self.connected:
                d.errback(IOError(self.last_error or str(err)
                                  or "connection error"))
            elif cancelled is not None and cancelled():
                d.errback(IOError(FLUSH_CANCELLED_MSG))
            elif done:
                d.callback(None)
            else:
                timed_call(200, poll)

        timed_call(0, poll)
        return d

    def _writer(self, stop):
        """ Dedicated writer thread: drains queued payloads strictly in
        order. Fatal errors mark the transport dead on the main thread
        (the submit loop then stops on its connected check). On cancel
        (disconnect/abort) the remaining queue was already dropped by
        _stop_keepalive().
        """
        cond = self._writer_cond
        queue = self._writer_queue
        #: disconnect() bumps the generation; our own abort path does
        #: not — that separates "torn down under us" (expected noise)
        #: from a real failure the user must see
        gen = self._generation
        while True:
            with cond:
                while not queue and not stop.is_set():
                    cond.wait(0.5)
                if stop.is_set():
                    break
                data = queue.popleft()
                self._writer_size = max(0, self._writer_size - len(data))
                #: flush() waits on this as well as the queue
                self._writer_active = True
            try:
                ok = self._drain_payload(data, stop)
            except Exception as e:
                with cond:
                    if self._generation == gen:
                        #: publish the failure in the same critical
                        #: section that clears the busy flag (QA-01):
                        #: flush() checks it before trusting idle()
                        self._writer_error = e
                    self._writer_active = False
                    cond.notify_all()
                if self._generation != gen:
                    log.debug("usb | writer cancelled during error "
                              "handling: {}".format(e))
                    break
                self._writer_failed(e, gen)
                return
            with cond:
                self._writer_active = False
                cond.notify_all()
            if ok is False:
                break   # cancelled mid-payload
        #: If a recovery reclaimed the handle in the moment disconnect()
        #: was releasing it, don't leak the claim. Generation-bound: a
        #: newer session already owns the transport once disconnect()
        #: has bumped the generation (a leaked claim self-heals on the
        #: next connect's reset recovery; clobbering a live session
        #: would not).
        if stop.is_set() and self._generation == gen:
            with self._lock:
                self._release()

    def _writer_failed(self, exc, gen):
        """ Fatal writer-thread error: make sure nothing is left claimed
        or queued, then mark the transport dead and tell the protocol —
        on the main thread. Runs on the writer thread. Generation-bound
        (`gen` is the writer's session): a stale writer must never mark
        a newer session dead.
        """
        if self._generation != gen:
            log.debug("usb | stale writer failure ignored: %s" % exc)
            return
        log.error("usb | writer failed: %s" % exc)
        try:
            with self._lock:
                self._release()
        except Exception:
            pass
        self._stop_keepalive()

        def mark_dead():
            if self._generation != gen:
                #: a newer session took over while this was queued
                return
            self.last_error = str(exc)
            was_connected = self.connected
            self.connected = False
            if was_connected:
                self.protocol.connection_lost()

        self._call_on_main(mark_dead)

    def _drain_payload(self, data, stop=None):
        """ Push one payload to the device, chunked, with flow control.

        A bulk timeout is flow control, not an error: pyusb 1.3.1
        (libusb1 backend) returns a SHORT COUNT when a timed-out
        transfer moved bytes and raises USBTimeoutError only when zero
        bytes were transferred, so retrying the same offset can neither
        drop nor duplicate data. A full CH554 ring buffer NAKs the
        endpoint while the cutter chews through queued moves — that can
        legitimately take minutes over a large job — so only a total
        lack of progress for NO_PROGRESS_ABORT_S (wedged firmware, or
        the panel offline/in origin mode) aborts the job.

        Runs on the writer thread (`stop` = its stop event) or inline on
        the calling thread (stop=None; tests and offline use). The lock
        is held per attempt, never across a whole chunk, so the
        keepalive and disconnect() can always interleave. Returns False
        when cancelled via `stop`.
        """
        #: Never the live Atom config: the UI can edit it mid-job
        p = self._params
        ep = p.endpoint if p is not None else self.config.endpoint
        step = max(1, p.chunk_size if p is not None
                   else self.config.chunk_size)
        last_progress = time.monotonic()
        stall_logged = last_progress
        for i in range(0, len(data), step):
            chunk = data[i:i + step]
            offset = 0
            attempt = 0
            while offset < len(chunk):
                if stop is not None and stop.is_set():
                    #: disconnect()/abort ended the session: stop
                    #: sending quietly, the initiator handles the state
                    return False
                now = time.monotonic()
                if now - last_progress >= NO_PROGRESS_ABORT_S:
                    self._abort_job(
                        "no write progress for %.0fs" % (now - last_progress))
                deadline = last_progress + NO_PROGRESS_ABORT_S
                abort_reason = None
                n = 0
                with self._lock:
                    #: Re-check after acquiring: disconnect() may have
                    #: cancelled while we waited for the lock, and not
                    #: one more claim or chunk may slip out then
                    if stop is not None and stop.is_set():
                        return False
                    # Phase 1: claim + CDC init. A failure here cannot
                    # have cut anything, so it takes the retry ladder,
                    # never the mid-transfer abort.
                    if self._dev is None:
                        try:
                            self._claim()
                        except (IOError, usb.core.USBError) as e:
                            attempt += 1
                            log.warning(
                                "usb | claim failed (attempt %d): %s"
                                % (attempt, e))
                            if attempt >= 3:
                                self._fail(e)
                            try:
                                self._recover(
                                    reset=attempt >= 2, deadline=deadline,
                                    cancelled=(stop.is_set if stop
                                               else None))
                            except Exception as e2:
                                log.warning(
                                    "usb | recovery failed: %s" % e2)
                                self._fail(e)
                        else:
                            #: The CDC handshake can take seconds:
                            #: disconnect() may have cancelled while it
                            #: ran, and its generation bump means the
                            #: writer's final cleanup would skip this
                            #: fresh claim — release it here, where the
                            #: lock is still held and ownership is
                            #: unambiguous
                            if stop is not None and stop.is_set():
                                self._release()
                                return False
                        continue

                    # Phase 2: bulk write. Short count -> resume from
                    # offset; timeout -> zero bytes moved, retry the
                    # same offset (flow control); any OTHER USBError ->
                    # abort: pyusb discards the transferred count for
                    # non-timeout failures, so this chunk's consumption
                    # is unknown and recovery + resend could duplicate
                    # cuts (only the claim phase above, where nothing
                    # was sent yet, keeps its retry ladder).
                    try:
                        n = self._dev.write(
                            ep, memoryview(chunk)[offset:],
                            timeout=WRITE_TIMEOUT_MS)
                    except usb.core.USBTimeoutError:
                        now = time.monotonic()
                        if now - stall_logged >= 5.0:
                            log.debug(
                                "usb | buffer full, waiting for the "
                                "cutter to drain (%.0fs without "
                                "progress)" % (now - last_progress))
                            stall_logged = now
                        continue
                    except usb.core.USBError as e:
                        abort_reason = ("bulk write failed "
                                        "mid-transfer: %s" % e)
                if abort_reason:
                    #: outside the lock: _abort_job acquires it itself
                    self._abort_job(abort_reason)
                if n:
                    offset += n
                    last_progress = time.monotonic()
                    stall_logged = last_progress
        return True

    def read(self, size=None):
        return b''

    def disconnect(self):
        # Always stop the keepalive, even if connected is already False
        # (e.g. after a failed write marked the transport dead)
        self._stop_keepalive()
        # Cancel any in-flight connect: bump the generation so its
        # callbacks refuse to complete and clean up the handle instead
        self._generation += 1
        was_connected = self.connected
        # Reset unconditionally: a wedged device must never leave the
        # transport looking "already connected" (see the raw transport bug)
        self.connected = False
        wt = self._writer_thread
        if not self._connecting and (wt is None or not wt.is_alive()):
            with self._lock:
                self._release()
        # else: the connect worker or a still-exiting writer (join timed
        # out above, e.g. inside a reset settle) owns the handle; their
        # generation-bound cleanup releases it — waiting on _lock here
        # could block the GUI for seconds
        if was_connected:
            self.protocol.connection_lost()

    def __repr__(self):
        config = self.config
        return "UsbTransport({:04x}:{:04x})".format(config.vid, config.pid)
