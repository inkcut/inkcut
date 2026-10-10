# -*- coding: utf-8 -*-
"""
Bluetooth LE transport.

Silhouette Cameo 4 (and relatives) expose their Graphtec/GPGL command
stream over a BLE GATT service rather than a classic Bluetooth serial
port, so pyserial cannot reach them. This transport talks to that
service using `bleak`.

bleak is asyncio based while Inkcut runs on a Qt/twisted reactor, so all
BLE work happens on a dedicated event loop in a background thread and is
bridged back to the reactor with Deferreds.
"""
import asyncio
import threading
import traceback

from atom.atom import set_default
from atom.api import Bool, Int, Instance, List, Str, Value
from inkcut.core.api import Model, log
from inkcut.device.plugin import DeviceTransport
from twisted.internet import defer, reactor
from twisted.python.failure import Failure


#: Silhouette Cameo 4 GATT service. Commands are written to DATA and the
#: machine reports status ("1" busy, "2" ready) back on STATUS.
CAMEO_SERVICE = 'e2088282-4fde-42f9-bb22-6ec3c7ed8f91'
CAMEO_STATUS = '61490654-b5b4-458c-a867-9e15bc1471e0'
CAMEO_DATA = '6d92661d-f429-4d67-929b-28e7a9780912'


def import_bleak():
    """ Import bleak, explaining how to get it if it is missing. """
    try:
        import bleak
    except ImportError:
        raise ImportError(
            'The Bluetooth LE transport needs the bleak package. '
            'Install it with "pip install bleak".')
    return bleak


#: Characteristics under this suffix are standard Bluetooth SIG ones
#: (device info, battery, ...), never the vendor command channel.
SIG_SUFFIX = '-0000-1000-8000-00805f9b34fb'


def discover_characteristics(client):
    """ Work out which characteristics carry commands and status.

    Returns (data_uuid, status_uuid), either of which may be None.

    The command channel is a vendor service with a writable
    characteristic. Machines like the Cameo 4 use a write-only
    characteristic for the command stream and a separate
    indicate/notify one for status, so prefer a characteristic that
    only writes and take the notifying one for status.

    """
    for service in client.services:
        if service.uuid.lower().endswith(SIG_SUFFIX):
            continue
        writable, notifying = [], []
        for char in service.characteristics:
            props = char.properties
            if 'write' in props or 'write-without-response' in props:
                writable.append(char)
            if 'indicate' in props or 'notify' in props:
                notifying.append(char)
        if not writable:
            continue
        write_only = [c for c in writable if c not in notifying]
        data = (write_only or writable)[0]
        status = notifying[0] if notifying else None
        log.debug('ble | discovered service {} data={} status={}'.format(
            service.uuid, data.uuid, status.uuid if status else None))
        return data.uuid, status.uuid if status else None
    return None, None


class BleWorker(object):
    """ Owns the asyncio loop that bleak runs on. """
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(
            target=self._run, name='inkcut-ble', daemon=True)
        self.thread.start()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coro):
        """ Schedule a coroutine and return a Deferred for its result. """
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        d = defer.Deferred()

        def done(f):
            try:
                result = f.result()
            except Exception as e:
                reactor.callFromThread(d.errback, Failure(e))
            else:
                reactor.callFromThread(d.callback, result)

        future.add_done_callback(done)
        return d


class BleDevice(object):
    """ A device found by a scan. """
    def __init__(self, address, name):
        self.address = address
        self.name = name or 'Unknown'

    def __repr__(self):
        return '{} ({})'.format(self.name, self.address)


class BLEConfig(Model):
    #: Address of the device. On macOS this is a CoreBluetooth UUID, on
    #: Linux/Windows it is the MAC address.
    address = Str().tag(config=True)

    #: Devices found by the last scan
    devices = List()

    #: True while a scan is running
    scanning = Bool()

    #: GATT characteristics to use. Defaults suit the Cameo 4, but are
    #: normally detected on connect rather than entered by hand.
    data_uuid = Str(CAMEO_DATA).tag(config=True)
    status_uuid = Str(CAMEO_STATUS).tag(config=True)

    #: Detect the characteristics from the device's GATT table instead
    #: of using the values above
    auto_discover = Bool(True).tag(config=True)

    #: GPGL commands are terminated with ETX. Inkcut's protocols do not
    #: add it, so do it here.
    append_etx = Bool(True).tag(config=True)

    #: Seconds to look for the device before giving up
    timeout = Int(20).tag(config=True)

    #: Bytes per GATT write
    chunk_size = Int(180).tag(config=True)

    #: Only list devices whose name contains one of these (comma
    #: separated, case insensitive). BLE adverts carry no service uuid
    #: for these machines, and macOS hides the hardware address behind a
    #: random per-host uuid, so the name is all there is to filter on.
    name_filter = Str('cameo,silhouette,portrait,curio').tag(config=True)

    #: List every device found instead of applying the filter
    show_all = Bool(False).tag(config=True)

    def matches_filter(self, device):
        """ True if the device should be listed. """
        if self.show_all:
            return True
        #: Never hide the device already selected
        if device.address == self.address:
            return True
        terms = [t.strip().lower() for t in self.name_filter.split(',')]
        terms = [t for t in terms if t]
        if not terms:
            return True
        name = (device.name or '').lower()
        return any(t in name for t in terms)

    def refresh(self):
        """ Scan for nearby BLE devices. """
        if self.scanning:
            return
        self.scanning = True

        async def scan():
            import_bleak()
            from bleak import BleakScanner
            found = await BleakScanner.discover(timeout=8.0, return_adv=True)
            return [BleDevice(addr, (d.name or adv.local_name))
                    for addr, (d, adv) in found.items()]

        def done(devices):
            total = len(devices)
            devices = [d for d in devices if self.matches_filter(d)]
            self.devices = sorted(devices, key=lambda d: d.name.lower())
            self.scanning = False
            log.debug('ble | scan found {} devices, {} listed'.format(
                total, len(devices)))

        def failed(failure):
            self.scanning = False
            log.error('ble | scan failed | {}'.format(failure))

        BleWorker.instance().submit(scan()).addCallbacks(done, failed)


class BLETransport(DeviceTransport):
    #: Default config
    config = Instance(BLEConfig, ()).tag(config=True)

    #: The bleak client
    client = Value()

    #: Serializes writes so commands arrive in order
    _lock = Value()

    #: Characteristics actually in use once connected
    _data_uuid = Str()
    _status_uuid = Str()

    #: Streams commands as they are generated, like a serial port
    always_spools = set_default(False)

    # -------------------------------------------------------------------------
    # Reactor-thread callbacks
    # -------------------------------------------------------------------------
    def _notify(self, sender, data):
        """ Called on the BLE thread when the machine reports status. """
        data = bytes(data)
        reactor.callFromThread(self._dispatch_read, data)

    def _dispatch_read(self, data):
        log.debug('<- {} | {}'.format(self, data))
        self.last_read = data
        if self.protocol is not None:
            self.protocol.data_received(data)

    def _dispatch_connected(self):
        self.connected = True
        if self.protocol is not None:
            self.protocol.connection_made()

    def _dispatch_disconnected(self):
        if not self.connected:
            return
        self.connected = False
        if self.protocol is not None:
            self.protocol.connection_lost()

    def _on_disconnect(self, client):
        reactor.callFromThread(self._dispatch_disconnected)

    def _apply_discovered(self, data_uuid, status_uuid):
        """ Show what was detected in the settings view. """
        if data_uuid:
            self.config.data_uuid = data_uuid
        self.config.status_uuid = status_uuid or ''

    # -------------------------------------------------------------------------
    # DeviceTransport API
    # -------------------------------------------------------------------------
    def connect(self):
        return BleWorker.instance().submit(self._connect())

    async def _connect(self):
        import_bleak()
        from bleak import BleakClient, BleakScanner
        config = self.config
        address = config.address
        if not address:
            raise IOError('No BLE device selected')
        try:
            #: A device stops advertising while something else holds a
            #: connection to it, so a scan will not see it. Fall back to
            #: connecting by address, which can reach a known peripheral.
            device = await BleakScanner.find_device_by_address(
                address, timeout=config.timeout)
            if device is None:
                log.debug('ble | {} not advertising, trying direct '
                          'connect'.format(address))
                device = address

            client = BleakClient(
                device, timeout=30.0,
                disconnected_callback=self._on_disconnect)
            try:
                await client.connect()
            except Exception as e:
                raise IOError(
                    'Could not connect to {}: {}. Check it is powered on, '
                    'in range, and not connected in another '
                    'application.'.format(address, e))

            data_uuid, status_uuid = config.data_uuid, config.status_uuid
            if config.auto_discover or not data_uuid:
                found_data, found_status = discover_characteristics(client)
                if found_data:
                    data_uuid, status_uuid = found_data, found_status
                    reactor.callFromThread(
                        self._apply_discovered, found_data, found_status)
                elif not data_uuid:
                    raise IOError(
                        'No writable characteristic found on {}. This '
                        'device does not look like a cutter.'.format(device))
                else:
                    log.warning('ble | discovery found nothing, using the '
                                'configured characteristics')
            self._data_uuid = data_uuid
            self._status_uuid = status_uuid or ''

            #: Status notifications are optional, not every machine has them
            if status_uuid:
                try:
                    await client.start_notify(status_uuid, self._notify)
                except Exception as e:
                    log.warning('ble | no status notifications | {}'.format(e))

            self.client = client
            self._lock = asyncio.Lock()
            log.debug('-- {} | connected'.format(self))
            reactor.callFromThread(self._dispatch_connected)
        except Exception:
            #: twisted can swallow these
            log.error('ble | {}'.format(traceback.format_exc()))
            raise

    def write(self, data):
        if not self.connected or self.client is None:
            raise IOError('BLE device is not connected')
        if hasattr(data, 'encode'):
            data = data.encode()
        if self.config.append_etx and not data.endswith(b'\x03'):
            data += b'\x03'
        log.debug('-> {} | {}'.format(self, data))
        self.last_write = data
        return BleWorker.instance().submit(self._write(data))

    async def _write(self, data):
        config = self.config
        client = self.client
        async with self._lock:
            for i in range(0, len(data), config.chunk_size):
                chunk = data[i:i + config.chunk_size]
                #: Must be a write *with* response; the Cameo ignores
                #: write-without-response entirely.
                await client.write_gatt_char(
                    self._data_uuid or config.data_uuid, chunk, response=True)

    def disconnect(self):
        if self.client is None:
            return
        return BleWorker.instance().submit(self._disconnect())

    async def _disconnect(self):
        client, self.client = self.client, None
        if client is None:
            return
        try:
            await client.disconnect()
        except Exception as e:
            log.warning('ble | disconnect | {}'.format(e))
        log.debug('-- {} | closed by request'.format(self))
        reactor.callFromThread(self._dispatch_disconnected)

    def __repr__(self):
        return 'ble://{}'.format(self.config.address or '?')
