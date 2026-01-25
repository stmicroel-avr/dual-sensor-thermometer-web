import asyncio
from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic

def callback(sender: BleakGATTCharacteristic, data: bytearray):
    print(f"{sender}: {data}")

async def add_device():
    client = BleakClient('D4611DE1-21B5-C5E0-C5C2-B5A93F945DAB')
    await client.connect()
    await client.start_notify('ffe1', callback)


# async def scan():
#     result_list = []
#     devices = await BleakScanner.discover(3)
#     for device in devices:
#         result_list.append({
#             'addr': device.address,
#             'name': device.name,
#         })
#     return result_list

if __name__ == "__main__":
    print("scan...")
    asyncio.run(add_device())
