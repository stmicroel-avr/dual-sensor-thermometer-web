import asyncio
from dataclasses import dataclass
from bleak import BleakScanner, BleakClient
from datetime import datetime
from fastapi import FastAPI

@dataclass
class Device:
    """
    Connected device
    """
    name: str|None
    address: str|None
    time: str|None

async def ble_scan(app: FastAPI):
    """
    Scan all available bluetooth devices
    :return: list
    """
    result_list = []
    devices = await BleakScanner.discover(10)
    for device in devices:
        result_list.append({
            'addr': device.address,
            'name': device.name,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        })
    result_list.sort(key=lambda x: (x['name'] is None, x['name'] or ''))
    app.state.logger.info(f"Found {len(result_list)} devices")

    return result_list

async def ble_connect_worker(app: FastAPI, address: str):
    """
    Bluetooth connection and handle new incoming data
    :param app: FastAPI
    :param address: Device address
    :return:
    """
    def on_rx(_, data: bytearray):
        app.state.queue.put_nowait(data.decode(errors="ignore"))

    client = BleakClient(address)
    await client.connect()
    app.state.logger.info(f"Connected to {address}")

    await client.start_notify("0000ffe1-0000-1000-8000-00805f9b34fb", on_rx)
    while True:
        await asyncio.sleep(0.1)