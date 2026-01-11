"""
routes/heartbeat.py - Heartbeat receiver endpoint

Devices post periodic heartbeats so the platform can:
- update last seen time and online/offline status
- track signal strength / metadata
- auto-enroll devices that aren't registered yet (MVP behavior)
"""

from datetime import datetime
from typing import Any, Dict

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from database import get_database
from models import HeartbeatData, HeartbeatResponse


router = APIRouter()


@router.post("/", response_model=HeartbeatResponse)
async def receive_heartbeat(payload: HeartbeatData) -> HeartbeatResponse:
    """
    Receive a heartbeat from a device.

    Uses logical device_id (like 'dev-001').
    If the device doesn't exist yet, it is auto-enrolled (basic defaults).
    """
    db = await get_database()

    now = datetime.utcnow()

    device = await db.devices.find_one({"deviceId": payload.device_id})

    if device is None:
        # Auto-enroll device (MVP)
        device_doc: Dict[str, Any] = {
            "deviceId": payload.device_id,
            "name": payload.device_id,
            "type": (payload.metadata or {}).get("type", "Unknown"),
            "ipAddress": payload.ip_address or "0.0.0.0",
            "status": payload.status,
            "lastSeen": now,
            "heartbeatInterval": 30,
            "alertsEnabled": True,
            "signalStrength": payload.signal_strength,
            "ipAddressHistory": [payload.ip_address] if payload.ip_address else [],
            "organization": None,
            "createdAt": now,
            "updatedAt": now,
        }
        await db.devices.insert_one(device_doc)

        return HeartbeatResponse(
            success=True,
            device_id=payload.device_id,
            status=device_doc["status"],
            message="Device auto-enrolled and heartbeat recorded",
            last_seen=device_doc["lastSeen"],
        )

    # Update existing device
    update_set: Dict[str, Any] = {
        "status": payload.status,
        "lastSeen": now,
        "updatedAt": now,
    }

    if payload.signal_strength is not None:
        update_set["signalStrength"] = payload.signal_strength

    update_ops: Dict[str, Any] = {"$set": update_set}

    if payload.ip_address and payload.ip_address != device.get("ipAddress"):
        update_set["ipAddress"] = payload.ip_address
        update_ops["$push"] = {"ipAddressHistory": payload.ip_address}
        
        # Check for suspicious IP change
        from services.security_monitor import get_security_monitor
        security_monitor = get_security_monitor()
        anomaly = await security_monitor.check_ip_change_anomaly(
            db,
            str(device["_id"]),
            payload.ip_address,
            device.get("ipAddress", "")
        )
        
        if anomaly and device.get("alertsEnabled", True):
            alert_doc = {
                "deviceId": device["_id"],
                "message": anomaly["reason"],
                "severity": anomaly["severity"],
                "type": "security",
                "context": anomaly,
                "resolved": False,
                "resolvedAt": None,
                "createdAt": now,
                "updatedAt": now,
            }
            await db.alerts.insert_one(alert_doc)

    await db.devices.update_one({"_id": device["_id"]}, update_ops)

    # Optional: create a lightweight system alert on device-reported error status (MVP)
    if payload.status == "error" and device.get("alertsEnabled", True):
        alert_doc = {
            "deviceId": ObjectId(device["_id"]),
            "message": "Device reported error status via heartbeat",
            "severity": "medium",
            "type": "system",
            "context": {"metadata": payload.metadata or {}},
            "resolved": False,
            "resolvedAt": None,
            "createdAt": now,
            "updatedAt": now,
        }
        await db.alerts.insert_one(alert_doc)

    return HeartbeatResponse(
        success=True,
        device_id=payload.device_id,
        status=payload.status,
        message="Heartbeat recorded",
        last_seen=now,
    )

