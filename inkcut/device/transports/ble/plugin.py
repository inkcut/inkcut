# -*- coding: utf-8 -*-
"""
Bluetooth LE transport.

For cutters that take their commands over a BLE GATT service, such as
the Silhouette Cameo 4. This transport talks to that service using
`bleak`, which runs on the application's asyncio event loop.

Which service and characteristics to use is set by the transport config.

    default_config = {
        'connection': {
            'ble': {
                'service_uuid': '...',
                'write_uuid': '...',
                'read_uuid': '...',
                'notify_uuid': '...',
                'append_etx': True,
            }
        }
    }

service_uuid and write_uuid are required. read_uuid is where the machine
answers queries, and notify_uuid where it reports status unasked; both
are optional. Replies on read_uuid go to the protocol like a serial
port's input. Status on notify_uuid is only logged, so that a "busy"
the machine sends unasked is not taken as the answer to a query. A
machine without a read_uuid answers on notify_uuid, which is then
treated as the reply stream.

Finding the values for a new cutter
-----------------------------------

A BLE device publishes a table of services, each holding
characteristics: slots that can be read, written, or that push data
back (notify/indicate). Every one is identified by a UUID, chosen by the
manufacturer, so the values below mean nothing outside that machine
family and have to be found by looking at the machine.

1. Make sure nothing else holds a connection to the cutter (the vendor's
   own app, a phone). A connected peripheral stops advertising, so a
   scan will not see it.

2. Dump its GATT table. A phone app such as nRF Connect or LightBlue
   shows it, or with bleak::

       import asyncio
       from bleak import BleakScanner, BleakClient

       async def main():
           found = await BleakScanner.discover(return_adv=True)
           for d, adv in found.values():
               print(d.address, d.name or adv.local_name)
           address = input('address: ')
           async with BleakClient(address) as client:
               for s in client.services:
                   print(s.uuid, s.description)
                   for c in s.characteristics:
                       print('   ', c.uuid, c.properties)

       asyncio.run(main())

   On macOS the address is a per-host UUID rather than the hardware
   address, so it differs between computers. Drivers should never
   include it.

3. Skip the standard services. Their UUIDs end in
   -0000-1000-8000-00805f9b34fb (device information, battery, ...). What
   is left is the vendor's service, usually only one. That is
   service_uuid.

4. Sort its characteristics by properties. The command channel accepts
   writes; a write-only one is the strongest candidate, and that is
   write_uuid. Replies and status come back on ones that can notify or
   indicate, which are read_uuid and notify_uuid.

   The properties do not always settle it. The Cameo 4 Plus reports::

       e2088282-4fde-42f9-bb22-6ec3c7ed8f91     vendor service
           61490654-b5b4-458c-a867-9e15bc1471e0 write, indicate  <- status
           8dcf199a-30e7-4bd4-beb6-beb57dca866c write, indicate  <- replies
           6d92661d-f429-4d67-929b-28e7a9780912 write            <- commands

   Two characteristics look the same, and only trying them shows which
   is which.

5. Confirm by experiment. Subscribe to every notify/indicate candidate
   (client.start_notify), then write commands to the write candidate
   that make the machine respond and do not cut. A Cameo answers GPGL
   "FG" (its name) and ESC ENQ (its state) on its reply characteristic,
   and on its status characteristic reports "1" (busy) then "0" or "2"
   (ready, with or without media loaded) whenever it moves, as for "H"
   (home). If nothing happens, vary how the command is sent:

   - write_with_response: some machines silently ignore writes without
     a response. The Cameo 4 is one of them.
   - append_etx: GPGL machines run a command once it is terminated by
     ETX (0x03). The GPGL protocol puts ETX before each command, so the
     latest one is only terminated by the next unless this is on.
   - chunk_size: large writes are split into chunks of this many bytes.
     Lower it if long jobs stall or the connection drops.

6. Put what worked in the driver's default_config as above, and add
   'ble' to its connections. Devices created from the driver after that
   get the values. Devices saved earlier keep a copy of the driver from
   when they were created, without the values, so they must be added
   again.

"""
import asyncio
import traceback

from atom.atom import set_default
from atom.api import Bool, Int, Instance, List, Str, Value
from inkcut.core.api import Model, log
from inkcut.device.plugin import DeviceTransport


def import_bleak():
    """ Import bleak, explaining how to get it if it is missing. """
    try:
        import bleak
    except ImportError:
        raise ImportError(
            'The Bluetooth LE transport needs the bleak package. '
            'Install it with "pip install bleak".')
    return bleak


def find_characteristics(services, config):
    """ Look up the configured characteristics on a connected device.

    Returns
    -------
    result: tuple
        (write, read, notify) characteristics. read and notify are None
        if the config has no read_uuid or notify_uuid.

    """
    service = services.get_service(config.service_uuid)
    if service is None:
        raise IOError('Service {} not found on the device'.format(
            config.service_uuid))
    chars = []
    for uuid in (config.write_uuid, config.read_uuid, config.notify_uuid):
        char = service.get_characteristic(uuid) if uuid else None
        if uuid and char is None:
            raise IOError('Characteristic {} not found in service {}'.format(
                uuid, config.service_uuid))
        chars.append(char)
    return tuple(chars)


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

    #: GATT service that carries the command stream. Set by the driver.
    service_uuid = Str().tag(config=True)

    #: Characteristic in that service commands are written to. Set by
    #: the driver.
    write_uuid = Str().tag(config=True)

    #: Characteristic in that service the machine answers queries on.
    #: Optional, not every machine answers.
    read_uuid = Str().tag(config=True)

    #: Characteristic in that service the machine reports status on
    #: unasked. Optional, not every machine reports status.
    notify_uuid = Str().tag(config=True)

    #: Terminate each write with ETX. The GPGL protocol puts ETX before
    #: each command, so the latest one is not terminated until the next
    #: is sent, and machines like the Cameo 4 wait for it.
    append_etx = Bool().tag(config=True)

    #: Use write with response. Some machines (e.g. the Cameo 4) ignore
    #: write-without-response entirely.
    write_with_response = Bool(True).tag(config=True)

    #: Seconds to look for the device before giving up
    timeout = Int(20).tag(config=True)

    #: Bytes per GATT write
    chunk_size = Int(180).tag(config=True)

    #: Only list devices whose name contains one of these (comma
    #: separated, case insensitive). BLE adverts from some machines carry
    #: no service uuid, and macOS hides the hardware address behind a
    #: random per-host uuid, so the name is all there is to filter on.
    name_filter = Str().tag(config=True)

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

    async def refresh(self):
        """ Scan for nearby BLE devices. """
        if self.scanning:
            return
        self.scanning = True
        try:
            import_bleak()
            from bleak import BleakScanner
            found = await BleakScanner.discover(timeout=8.0, return_adv=True)
            devices = [BleDevice(addr, (d.name or adv.local_name))
                       for addr, (d, adv) in found.items()]
            listed = [d for d in devices if self.matches_filter(d)]
            self.devices = sorted(listed, key=lambda d: d.name.lower())
            log.debug('ble | scan found {} devices, {} listed'.format(
                len(devices), len(listed)))
        except Exception:
            log.error('ble | scan failed | {}'.format(traceback.format_exc()))
        finally:
            self.scanning = False


class BLETransport(DeviceTransport):
    #: Default config
    config = Instance(BLEConfig, ()).tag(config=True)

    #: The bleak client
    client = Value()

    #: Serializes writes so commands arrive in order
    _lock = Instance(asyncio.Lock, ())

    #: The connect in progress. Each jog asks to connect while one is
    #: still running, and two connects leave two clients on one machine,
    #: so later requests wait for this one and share its result.
    _connecting = Value()

    #: Characteristic commands are written to once connected
    _write_char = Value()

    #: Whether replies come on their own characteristic, so that status
    #: notifications can be kept out of the reply stream
    _has_read_char = Bool()

    #: Streams commands as they are generated, like a serial port
    always_spools = set_default(False)

    # -------------------------------------------------------------------------
    # bleak callbacks
    # -------------------------------------------------------------------------
    def _on_read(self, sender, data):
        """ Called when the machine answers a query. """
        data = bytes(data)
        log.debug('<- {} | {}'.format(self, data))
        self.last_read = data
        if self.protocol is not None:
            self.protocol.data_received(data)

    def _on_notify(self, sender, data):
        """ Called when the machine reports status unasked. """
        if not self._has_read_char:
            #: Machines without a reply characteristic answer here
            return self._on_read(sender, data)
        log.debug('<- {} | status {}'.format(self, bytes(data)))

    def _on_disconnect(self, client):
        if client is not self.client:
            return
        self.client = None
        self.connected = False
        log.debug('-- {} | dropped'.format(self))

    # -------------------------------------------------------------------------
    # DeviceTransport API
    # -------------------------------------------------------------------------
    async def connect(self):
        if self.connected:
            return
        task = self._connecting
        if task is None or task.done():
            task = self._connecting = asyncio.ensure_future(self._connect())
        #: Shielded so a caller giving up does not cancel it for the rest
        await asyncio.shield(task)

    async def _connect(self):
        import_bleak()
        from bleak import BleakClient, BleakScanner
        config = self.config
        address = config.address
        try:
            if not address:
                raise IOError('No BLE device selected')
            if not config.service_uuid or not config.write_uuid:
                raise IOError(
                    'No Bluetooth LE service is set for this device. Its '
                    'driver must provide service_uuid and write_uuid. A '
                    'device added before its driver did must be added '
                    'again.')

            #: A BLE connection can only be made to a device that is
            #: advertising, so it has to be found by a scan first, even
            #: with a saved address. A device stops advertising while
            #: something else holds a connection to it.
            device = await BleakScanner.find_device_by_address(
                address, timeout=config.timeout)
            if device is None:
                raise IOError(
                    '{} was not found. Make sure it is switched on and in '
                    'range, and disconnect it from any other application '
                    'or phone. A connected cutter cannot be seen.'.format(
                        address))

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

            try:
                write_char, read_char, notify_char = find_characteristics(
                    client.services, config)
                #: Without replies the protocol cannot query the machine
                if read_char is not None:
                    await client.start_notify(read_char, self._on_read)
            except Exception:
                await client.disconnect()
                raise
            self._write_char = write_char
            self._has_read_char = read_char is not None

            #: Status notifications are optional, not every machine has them
            if notify_char is not None:
                try:
                    await client.start_notify(notify_char, self._on_notify)
                except Exception as e:
                    log.warning('ble | no status notifications | {}'.format(e))

            self.client = client
            self.connected = True
            log.debug('-- {} | connected'.format(self))
            await self.protocol.init()
        except Exception:
            #: Make sure to log any issues as these tracebacks can get
            #: squashed
            log.error('ble | {}'.format(traceback.format_exc()))
            raise

    async def write(self, data):
        client = self.client
        if not self.connected or client is None:
            raise IOError('BLE device is not connected')
        config = self.config
        if hasattr(data, 'encode'):
            data = data.encode()
        if config.append_etx and not data.endswith(b'\x03'):
            data += b'\x03'
        log.debug('-> {} | {}'.format(self, data))
        self.last_write = data
        async with self._lock:
            for i in range(0, len(data), config.chunk_size):
                await client.write_gatt_char(
                    self._write_char, data[i:i + config.chunk_size],
                    response=config.write_with_response)

    async def disconnect(self):
        client, self.client = self.client, None
        if client is None:
            return
        try:
            await client.disconnect()
        except Exception as e:
            log.warning('ble | disconnect | {}'.format(e))
        self.connected = False
        log.debug('-- {} | closed by request'.format(self))

    def __repr__(self):
        return 'ble://{}'.format(self.config.address or '?')
