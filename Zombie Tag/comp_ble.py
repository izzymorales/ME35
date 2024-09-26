import asyncio
from bleak import BleakScanner

def callback(device_info, advertising_data):
    if device_info.name:
        if '$$' in device_info.name:
            print(device_info.name)
            
async def main():
    async with BleakScanner(callback) as scanner:
        await asyncio.sleep(0.1)
        
async def main2():
    while True:
        devices = await BleakScanner.discover(timeout = 1)
        for device_info in devices:
            if device_info.name:
                if '$$' in device_info.name:
                    print(device_info.name)
        await asyncio.sleep(0.1)
        
asyncio.run(main2())
