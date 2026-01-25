from bleak import BleakScanner

async def ble_scan():
    """
    Scan all available bluetooth devices
    :return: list
    """
    result_list = []
    devices = await BleakScanner.discover()
    for device in devices:
        result_list.append({
            'addr': device.address,
            'name': device.name,
        })
    return result_list


