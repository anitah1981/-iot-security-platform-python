"""
routes/heartbeat.py - Heartbeat receiver endpoint

Devices post periodic heartbeats so the platform can:
- update last seen time and online/offline status
- track signal strength / metadata
- auto-enroll devices that aren't registered yet (MVP behavior)

When X-API-Key header is present (device agent key from Settings), devices are associated
with that user/family and appear in the app. Without the key, heartbeats still work but
auto-enrolled devices are not tied to any account.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

from database import get_database
from models import HeartbeatData, HeartbeatResponse
from services.device_agent_key_service import get_user_by_api_key


router = APIRouter()


async def _heartbeat_api_key_user(request: Request) -> Optional[dict]:
    """Resolve X-API-Key header to user (or None). Used to associate devices with account."""
    raw = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not raw:
        return None
    return await get_user_by_api_key(raw)


@router.post("/", response_model=HeartbeatResponse)
async def receive_heartbeat(
    payload: HeartbeatData,
    request: Request,
    api_key_user: Optional[dict] = Depends(_heartbeat_api_key_user),
) -> HeartbeatResponse:
    """
    Receive a heartbeat from a device or from the device agent.

    Uses logical device_id (e.g. 'ring-front-door'). If the device doesn't exist yet,
    it is auto-enrolled. Send X-API-Key with your device agent API key (from Settings)
    so devices are linked to your account and appear in the app.
    """
    db = await get_database()
    now = datetime.utcnow()

    device = await db.devices.find_one({"deviceId": payload.device_id})

    if device is None:
        # Auto-enroll device – associate with user/family when API key provided
        user_id: Optional[ObjectId] = None
        family_id: Optional[ObjectId] = None
        if api_key_user:
            user_id = api_key_user["_id"] if isinstance(api_key_user["_id"], ObjectId) else ObjectId(api_key_user["_id"])
            family_id = api_key_user.get("_family_id")

        device_doc: Dict[str, Any] = {
            "deviceId": payload.device_id,
            "name": (payload.metadata or {}).get("name") or payload.device_id,
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
        if user_id is not None:
            device_doc["userId"] = user_id
            device_doc["user_id"] = user_id
        if family_id is not None:
            device_doc["family_id"] = family_id
        await db.devices.insert_one(device_doc)

        return HeartbeatResponse(
            success=True,
            device_id=payload.device_id,
            status=device_doc["status"],
            message="Device auto-enrolled and heartbeat recorded",
            last_seen=device_doc["lastSeen"],
        )

    # When API key is used, only allow updating devices that belong to this user/family (or claim orphan devices)
    user_id_obj: Optional[ObjectId] = None
    family_id_obj: Optional[ObjectId] = None
    if api_key_user:
        user_id_obj = api_key_user["_id"] if isinstance(api_key_user["_id"], ObjectId) else ObjectId(api_key_user["_id"])
        family_id_obj = api_key_user.get("_family_id")
        device_user = device.get("userId") or device.get("user_id")
        device_family = device.get("family_id")
        if device_user is not None or device_family is not None:
            if (device_user != user_id_obj and device_family != family_id_obj):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Device does not belong to this account",
                )
        # else: device has no owner (orphan) — we'll set userId/family_id below to claim it

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

    # Claim orphan device when updating with API key
    if user_id_obj is not None and (device.get("userId") is None and device.get("user_id") is None):
        update_set["userId"] = user_id_obj
        update_set["user_id"] = user_id_obj
    if family_id_obj is not None and device.get("family_id") is None:
        update_set["family_id"] = family_id_obj

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

