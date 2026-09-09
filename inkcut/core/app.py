"""
Copyright (c) 2020, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.
"""
import asyncio
import logging
import os
import signal
import sys
from inspect import iscoroutinefunction
from typing import Any, Callable, Optional

from asyncqtpy import QEventLoop, QEventLoopPolicy
from atom.api import Bool, Instance, Set, Typed
from enaml.qt import QT_API
from enaml.qt.qt_application import QtApplication
from enaml.qt.QtCore import Qt, QTimer
from enaml.qt.QtWidgets import QApplication

from .utils import log

class AsyncApplication(QtApplication):
    """Add asyncio support"""

    #: The Qt implementation of the asyncio event loop
    loop = Instance(QEventLoop, factory=asyncio.get_event_loop)

    #: Set of background tasks scheduled
    tasks = Set(asyncio.Task)

    running = Bool()

    def __init__(self, platform: Optional[str] = None):
        super().__init__(platform)
        asyncio.set_event_loop_policy(QEventLoopPolicy())
        assert self.loop is not None

        # Set logger level
        for name in logging.root.manager.loggerDict:
            if name.startswith("asyncqt"):
                log = logging.getLogger(name)
                log.setLevel(logging.WARN)

    def start(self):
        """Run using the event loop"""
        log.info("Application starting")
        loop = self.loop
        loop.set_exception_handler(self.on_async_exception)
        try:
            self.running = True
            with loop:
                loop.run_forever()
        finally:
            self.running = False

    def on_async_exception(self, loop, context):
        """Exception handler that ignores"""
        return loop.default_exception_handler(context)

    def deferred_call(self, callback: Callable, *args: Any, **kwargs: Any):
        """Invoke a callable on the next cycle of the main event loop
        thread. If the callback is an async function, schedule it as a
        background task.

        Parameters
        ----------
        callback : callable
            The callable object to execute at some point in the future.

        args, kwargs
            Any additional positional and keyword arguments to pass to
            the callback.

        """
        if iscoroutinefunction(callback) or kwargs.pop("async_", None):
            task = self.loop.create_task(callback(*args, **kwargs))
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)
            return task
        return super().deferred_call(callback, *args, **kwargs)

    def timed_call(self, ms: float, callback: Callable, *args: Any, **kwargs: Any):
        """Invoke a callable on the main event loop thread at a
        specified time in the future.

        Parameters
        ----------
        ms : int
            The time to delay, in milliseconds, before executing the
            callable.

        callback : callable
            The callable object to execute at some point in the future.

        args, kwargs
            Any additional positional and keyword arguments to pass to
            the callback.

        """
        if iscoroutinefunction(callback) or kwargs.pop("async_", None):
            return super().timed_call(ms, self.deferred_call, callback, *args, **kwargs)
        return super().timed_call(ms, callback, *args, **kwargs)
