import os
import sys
import asyncio
import pytest

from inkcut.device.protocols.hpgl import HPGLProtocol
from inkcut.device.transports.printer.plugin import (
    PrinterTransport, CupsPrinterConfig
)

pytestmark = pytest.mark.skipif(
    sys.platform == 'win32', reason="LPR is only used on Linux/macOS")

FAKE_LPR = """#!/bin/sh
echo "$@" > "{out}/lpr.args"
cat > "{out}/lpr.data"
"""


@pytest.fixture
def fake_lpr(tmp_path, monkeypatch):
    """ Put an `lpr` first on PATH that records its args and stdin """
    lpr = tmp_path / 'lpr'
    lpr.write_text(FAKE_LPR.format(out=tmp_path))
    lpr.chmod(0o755)
    monkeypatch.setenv('PATH', str(tmp_path), prepend=os.pathsep)
    return tmp_path


async def test_lpr_transport(fake_lpr):
    protocol = HPGLProtocol(scale=1)
    transport = PrinterTransport(
        protocol=protocol, config=CupsPrinterConfig(printer='secabo'))

    #: Used to hang forever because lpr was never started
    await asyncio.wait_for(transport.connect(), 5)
    await protocol.move(3, 2, 1)
    await asyncio.wait_for(transport.disconnect(), 5)

    #: Let LPRProtocol.process_exited run
    await asyncio.sleep(0)
    assert not transport.connected

    args = (fake_lpr / 'lpr.args').read_text().split()
    assert args == ['-P', 'secabo', '-o', 'raw']

    #: The whole job reached lpr's stdin before it exited
    assert (fake_lpr / 'lpr.data').read_bytes() == b"IN;PD3,2;"
