import asyncio
from bleak import BleakScanner

TARGET_NAME = "Mi Smart Magic Cube"
TARGET_SERVICE = "0000fe95-0000-1000-8000-00805f9b34fb"
SCAN_SECONDS = 15

seen = set()

def fmt_uuid(u):
    return str(u).lower()

def on_device(device, adv):
    addr = device.address
    if addr in seen:
        return
    seen.add(addr)

    name = device.name or adv.local_name or "(no name)"
    rssi = getattr(adv, 'rssi', None)
    rssi_str = f"RSSI={rssi}" if rssi is not None else "RSSI=?"
    services = [fmt_uuid(s) for s in (adv.service_uuids or [])]
    has_fe95 = TARGET_SERVICE in services
    is_mi = TARGET_NAME in name

    flag = ""
    if is_mi:
        flag += " [MI CUBE]"
    if has_fe95:
        flag += " [FE95]"

    print(f"{addr}  {rssi_str}  name={name}{flag}")
    if adv.manufacturer_data:
        for k, v in adv.manufacturer_data.items():
            print(f"    Manufacturer Data [{k:04X}]: {v.hex()}")
    if services:
        print(f"    Services: {', '.join(services)}")

async def main():
    print(f"Scanning BLE for {SCAN_SECONDS} seconds...")
    print(f"Looking for name='{TARGET_NAME}' and service {TARGET_SERVICE}")
    print()
    async with BleakScanner(on_device) as scanner:
        await asyncio.sleep(SCAN_SECONDS)
    print(f"\nDone. Total unique devices seen: {len(seen)}")

if __name__ == "__main__":
    asyncio.run(main())
