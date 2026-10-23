"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.
"""
import asyncio
import logging
from inkcut.core.api import Plugin, log

def patch_iostream():
    """IOStream _thread_main is broken if the loop is already running"""
    from ipykernel.iostream import IOPubThread

    def _thread_main(self):
        """The inner loop that's actually run in a thread"""

        def _start_event_gc():
            self._event_pipe_gc_task = asyncio.ensure_future(self._run_event_pipe_gc())

        self.io_loop.call_later(0, _start_event_gc)

        if not self._stopped:
            # avoid race if stop called before start thread gets here
            # probably only comes up in tests
            self.io_loop.start()

        if self._event_pipe_gc_task is not None:
            # cancel gc task to avoid pending task warnings
            async def _cancel():
                self._event_pipe_gc_task.cancel()  # type: ignore[union-attr]

            if not self._stopped:
                self.io_loop.run_sync(_cancel)
            else:
                self._event_pipe_gc_task.cancel()

        # self.io_loop.close(all_fds=True)

    IOPubThread._thread_main = _thread_main


def patch_ipykernel():
    from ipykernel.inprocess.client import InProcessKernelClient

    def _dispatch_to_kernel(self, msg):
        """Send a message to the kernel and handle a reply."""
        kernel = self.kernel
        if kernel is None:
            msg = "Cannot send request. No kernel exists."
            raise RuntimeError(msg)

        stream = kernel.shell_stream
        self.session.send(stream, msg)
        msg_parts = stream.recv_multipart()
        # Already in an event loop
        # if run_sync is not None:
        #     dispatch_shell = run_sync(kernel.dispatch_shell)
        #     dispatch_shell(msg_parts)
        # else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(kernel.dispatch_shell(msg_parts))
        idents, reply_msg = self.session.recv(stream, copy=False)
        self.shell_channel.call_handlers_later(reply_msg)

    InProcessKernelClient._dispatch_to_kernel = _dispatch_to_kernel


class ConsolePlugin(Plugin):
    def is_supported(self):
        try:
            from enaml.qt import qt_ipython_console
            return True
        except ImportError as e:
            log.warning("IPython console plugin is missing dependencies")
            log.exception(e)
            return False

    def start(self):
        """ Set the log level for IPython stuff to warn """
        patch_iostream()
        patch_ipykernel()
        for name in ['ipykernel.inprocess.ipkernel', 'traitlets']:
            log = logging.getLogger(name)
            log.setLevel(logging.WARNING)
