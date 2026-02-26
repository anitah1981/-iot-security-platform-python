"""
Add Test Data Script
Creates sample devices and alerts for testing dashboard charts
"""

import asyncio
import sys
from datetime import datetime, timedelta
from bson import ObjectId
from database import init_db, get_database, close_db
import os
from dotenv import load_dotenv

load_dotenv()

async def add_test_data():
    """Add test devices and alerts"""
    
    # Connect to database
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/iot_security")
    await init_db(mongo_uri)
    db = await get_database()
    
    # Get your user ID
    user = await db.users.find_one({"email": "anitah1981@gmail.com"})
    if not user:
        print("ERROR: User not found. Please make sure you're logged in first.")
        return
    
    user_id = user["_id"]
    print(f"Found user: {user['name']} ({user['email']})")
    
    # Check if devices already exist
    existing_devices = await db.devices.find({"user_id": user_id}).to_list(10)
    if existing_devices:
        print(f"\nFound {len(existing_devices)} existing devices. Using those for alerts.")
        device_ids = [d["_id"] for d in existing_devices]
        devices = existing_devices
    else:
        device_ids = []
    
    print("\n[INFO] Adding test data...")
    
    # Create test devices
    devices = [
        {
            "name": "Living Room Camera",
            "type": "Camera",
            "deviceId": "dev-cam-001",
            "ipAddress": "192.168.1.101",
            "status": "online",
            "lastSeen": datetime.utcnow(),
            "heartbeatInterval": 30,
            "alertsEnabled": True,
            "signalStrength": -45,
            "ipAddressHistory": ["192.168.1.101"],
            "user_id": user_id,
            "createdAt": datetime.utcnow() - timedelta(days=30),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Front Door Sensor",
            "type": "Sensor",
            "deviceId": "dev-sensor-001",
            "ipAddress": "192.168.1.102",
            "status": "online",
            "lastSeen": datetime.utcnow() - timedelta(minutes=2),
            "heartbeatInterval": 30,
            "alertsEnabled": True,
            "signalStrength": -52,
            "ipAddressHistory": ["192.168.1.102"],
            "user_id": user_id,
            "createdAt": datetime.utcnow() - timedelta(days=25),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "WiFi Router",
            "type": "Router",
            "deviceId": "dev-router-001",
            "ipAddress": "192.168.1.1",
            "status": "online",
            "lastSeen": datetime.utcnow(),
            "heartbeatInterval": 60,
            "alertsEnabled": True,
            "signalStrength": None,
            "ipAddressHistory": ["192.168.1.1"],
            "user_id": user_id,
            "createdAt": datetime.utcnow() - timedelta(days=60),
            "updatedAt": datetime.utcnow()
        },
        {
            "name": "Garage Door Opener",
            "type": "Sensor",
            "deviceId": "dev-garage-001",
            "ipAddress": "192.168.1.103",
            "status": "offline",
            "lastSeen": datetime.utcnow() - timedelta(hours=2),
            "heartbeatInterval": 30,
            "alertsEnabled": True,
            "signalStrength": -78,
            "ipAddressHistory": ["192.168.1.103"],
            "user_id": user_id,
            "createdAt": datetime.utcnow() - timedelta(days=20),
            "updatedAt": datetime.utcnow() - timedelta(hours=2)
        },
        {
            "name": "Smart Thermostat",
            "type": "Sensor",
            "deviceId": "dev-thermo-001",
            "ipAddress": "192.168.1.104",
            "status": "online",
            "lastSeen": datetime.utcnow() - timedelta(minutes=5),
            "heartbeatInterval": 60,
            "alertsEnabled": True,
            "signalStrength": -48,
            "ipAddressHistory": ["192.168.1.104"],
            "user_id": user_id,
            "createdAt": datetime.utcnow() - timedelta(days=15),
            "updatedAt": datetime.utcnow()
        }
    ]
    
    # Insert devices (only if they don't exist)
    if not existing_devices:
        for device in devices:
            result = await db.devices.insert_one(device)
            device_ids.append(result.inserted_id)
            print(f"[OK] Created device: {device['name']} ({device['type']})")
        print(f"\n[OK] Created {len(devices)} devices")
    else:
        print(f"\n[OK] Using {len(existing_devices)} existing devices")
    
    # Create test alerts (spread over last 30 days)
    alerts = []
    alert_types = ["connectivity", "security", "system", "power"]
    severities = ["low", "medium", "high", "critical"]
    
    # Generate alerts for each device
    for i, device_id in enumerate(device_ids):
        device = devices[i]
        
        # Critical alert (recent)
        alerts.append({
            "user_id": user_id,
            "device_id": device_id,
            "message": f"{device['name']} went offline unexpectedly",
            "severity": "critical",
            "type": "connectivity",
            "resolved": False,
            "context": {"ip": device["ipAddress"], "last_seen": device["lastSeen"].isoformat()},
            "created_at": datetime.utcnow() - timedelta(hours=2),
            "updated_at": datetime.utcnow() - timedelta(hours=2)
        })
        
        # High alert (yesterday)
        alerts.append({
            "user_id": user_id,
            "device_id": device_id,
            "message": f"Suspicious activity detected on {device['name']}",
            "severity": "high",
            "type": "security",
            "resolved": True,
            "resolved_at": datetime.utcnow() - timedelta(hours=12),
            "context": {"source_ip": "192.168.1.200"},
            "created_at": datetime.utcnow() - timedelta(days=1),
            "updated_at": datetime.utcnow() - timedelta(hours=12)
        })
        
        # Medium alerts (last week)
        for j in range(2):
            alerts.append({
                "user_id": user_id,
                "device_id": device_id,
                "message": f"{device['name']} signal strength low",
                "severity": "medium",
                "type": "system",
                "resolved": j == 0,  # First one resolved
                "resolved_at": datetime.utcnow() - timedelta(days=3) if j == 0 else None,
                "context": {"signal": device.get("signalStrength", -70)},
                "created_at": datetime.utcnow() - timedelta(days=3+j),
                "updated_at": datetime.utcnow() - timedelta(days=3+j)
            })
        
        # Low alerts (last 2 weeks)
        for j in range(3):
            alerts.append({
                "user_id": user_id,
                "device_id": device_id,
                "message": f"{device['name']} routine maintenance check",
                "severity": "low",
                "type": "system",
                "resolved": True,
                "resolved_at": datetime.utcnow() - timedelta(days=5+j),
                "context": {},
                "created_at": datetime.utcnow() - timedelta(days=7+j),
                "updated_at": datetime.utcnow() - timedelta(days=5+j)
            })
    
    # Check if alerts already exist
    existing_alerts_count = await db.alerts.count_documents({"user_id": user_id})
    if existing_alerts_count > 0:
        print(f"\n[INFO] You already have {existing_alerts_count} alerts.")
        print("[INFO] Adding more test alerts...")
    
    # Insert alerts
    await db.alerts.insert_many(alerts)
    print(f"[OK] Created {len(alerts)} new alerts")
    
    # Summary
    print("\n" + "="*50)
    print("[SUCCESS] TEST DATA ADDED!")
    print("="*50)
    print(f"Devices: {len(devices)}")
    online_count = len([d for d in devices if d.get('status') == 'online'])
    print(f"   - Online: {online_count}")
    print(f"   - Offline: {len(devices) - online_count}")
    print(f"Alerts: {len(alerts)} new alerts added")
    print(f"   - Critical: {len([a for a in alerts if a['severity'] == 'critical'])}")
    print(f"   - High: {len([a for a in alerts if a['severity'] == 'high'])}")
    print(f"   - Medium: {len([a for a in alerts if a['severity'] == 'medium'])}")
    print(f"   - Low: {len([a for a in alerts if a['severity'] == 'low'])}")
    print("\n[INFO] Refresh your dashboard to see the charts!")
    print("   URL: http://localhost:8000/dashboard")
    print("="*50)
    
    await close_db()

if __name__ == "__main__":
    asyncio.run(add_test_data())
