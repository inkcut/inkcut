# -*- coding: utf-8 -*-
"""
Actions for the cut settings pane that talk to the machine outside a job.

Like jogging, they connect if needed and leave the connection open.
"""
import traceback

from inkcut.core.api import log


async def connected_protocol(device):
    if not device.connection.connected:
        await device.connect()
    return device.connection.protocol


async def refresh_tools(device):
    """ Ask the machine which tools are loaded. """
    try:
        with device.device_busy():
            protocol = await connected_protocol(device)
            await protocol.get_tools()
    except Exception:
        log.error('cut | refresh tools | {}'.format(traceback.format_exc()))


async def set_autoblade_depth(device):
    """ Turn the AutoBlade to the configured depth now. """
    try:
        with device.device_busy():
            protocol = await connected_protocol(device)
            await protocol.set_autoblade_depth(protocol.config.autoblade_depth)
    except Exception:
        log.error('cut | set depth | {}'.format(traceback.format_exc()))
