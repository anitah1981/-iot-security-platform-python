import asyncio
from database import get_database, init_db
import os

async def check_devices():
    # Initialize database
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("ERROR: MONGO_URI not set")
        return
    
    await init_db(mongo_uri)
    db = await get_database()
    
    # Get all devices
    devices = await db.devices.find({"isDeleted": {"$ne": True}}).to_list(length=None)
    
    print(f"\n=== Found {len(devices)} device(s) ===\n")
    
    for d in devices:
        print(f"Device: {d.get('name')}")
        print(f"  ID: {d.get('deviceId')}")
        print(f"  IP: {d.get('ipAddress')}")
        print(f"  Status: {d.get('status')}")
        print(f"  Last Seen: {d.get('lastSeen')}")
        print(f"  Alerts Enabled: {d.get('alertsEnabled')}")
        print()

if __name__ == "__main__":
    asyncio.run(check_devices())
