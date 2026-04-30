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


def _is_likely_router_ip(ip: str) -> bool:
    """Treat IP as router/gateway so we never store it as a device IP (avoids false 'IP changed to router' alerts)."""
    if not ip or ip in ("0.0.0.0", "127.0.0.1"):
        return True
    parts = ip.strip().split(".")
    if len(parts) != 4:
        return False
    try:
        last_octet = int(parts[3])
        if last_octet == 1:
            return True  # Common gateway in .x.1
    except ValueError:
        pass
    return False


async def _is_user_router_ip(db, user_id: Optional[ObjectId], ip: str) -> bool:
    """True if ip matches the user's configured router/gateway IP."""
    if not ip or not user_id:
        return False
    settings = await db.network_settings.find_one({"userId": user_id})
    router = (settings or {}).get("routerIp") or (settings or {}).get("router_ip")
    return bool(router and (ip.strip() == router.strip()))


async def _heartbeat_api_key_user(request: Request) -> Optional[dict]:
    """Resolve X-API-Key header to user (or None). Used to associate devices with account."""
    raw = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not raw:
        return None
    return await get_user_by_api_key(raw)


def _owner_id_for_heartbeat(family_id: Optional[ObjectId], user_id: ObjectId) -> ObjectId:
    """Same namespace as device registration: family_id if in a family, else user_id."""
    return family_id if family_id is not None else user_id


async def _find_device_for_heartbeat(
    db,
    device_id: str,
    api_key_user: Optional[dict],
) -> Optional[Dict[str, Any]]:
    """
    Resolve device row in a tenant-safe way. With API key, scope by owner_id (or legacy user/family fields).
    Without API key, only match devices with no owner (orphan MVP).
    """
    if api_key_user:
        user_id_obj = api_key_user["_id"] if isinstance(api_key_user["_id"], ObjectId) else ObjectId(api_key_user["_id"])
        family_id_obj: Optional[ObjectId] = api_key_user.get("_family_id")
        family_oid = family_id_obj
        owner_id = _owner_id_for_heartbeat(family_oid, user_id_obj)

        doc = await db.devices.find_one(
            {
                "deviceId": device_id,
                "owner_id": owner_id,
                "isDeleted": {"$ne": True},
            }
        )
        if doc:
            return doc
        # Legacy documents before owner_id backfill
        owner_match: list[dict[str, Any]] = []
        if family_oid is not None:
            owner_match.append({"family_id": family_oid})
        owner_match.extend(
            [
                {"userId": user_id_obj},
                {"user_id": user_id_obj},
            ]
        )
        return await db.devices.find_one(
            {
                "deviceId": device_id,
                "isDeleted": {"$ne": True},
                "$and": [
                    {"$or": [{"owner_id": {"$exists": False}}, {"owner_id": None}]},
                    {"$or": owner_match},
                ],
            }
        )

    return await db.devices.find_one(
        {
            "deviceId": device_id,
            "userId": None,
            "user_id": None,
            "family_id": None,
            "isDeleted": {"$ne": True},
        }
    )


async def _registered_device_exists_without_api_key(db, device_id: str) -> bool:
    """True if any owned device uses this logical deviceId (heartbeats then require X-API-Key)."""
    doc = await db.devices.find_one(
        {
            "deviceId": device_id,
            "isDeleted": {"$ne": True},
            "$or": [
                {"userId": {"$exists": True, "$ne": None}},
                {"user_id": {"$exists": True, "$ne": None}},
                {"family_id": {"$exists": True, "$ne": None}},
            ],
        }
    )
    return doc is not None


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

    if not api_key_user and await _registered_device_exists_without_api_key(db, payload.device_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="X-API-Key required for this device",
        )

    device = await _find_device_for_heartbeat(db, payload.device_id, api_key_user)

    if device is None:
        # Auto-enroll device – associate with user/family when API key provided
        user_id: Optional[ObjectId] = None
        family_id: Optional[ObjectId] = None
        owner_id_val: Optional[ObjectId] = None
        if api_key_user:
            user_id = api_key_user["_id"] if isinstance(api_key_user["_id"], ObjectId) else ObjectId(api_key_user["_id"])
            family_id = api_key_user.get("_family_id")
            owner_id_val = _owner_id_for_heartbeat(family_id, user_id)

        # Never store router/gateway IP as device IP (avoids false "IP changed to router" alerts)
        device_ip = payload.ip_address
        if device_ip and (_is_likely_router_ip(device_ip) or await _is_user_router_ip(db, user_id, device_ip)):
            device_ip = None
        device_doc: Dict[str, Any] = {
            "deviceId": payload.device_id,
            "name": (payload.metadata or {}).get("name") or payload.device_id,
            "type": (payload.metadata or {}).get("type", "Unknown"),
            "ipAddress": device_ip or "0.0.0.0",
            "status": payload.status,
            "lastSeen": now,
            "heartbeatInterval": 30,
            "alertsEnabled": True,
            "signalStrength": payload.signal_strength,
            "ipAddressHistory": [device_ip] if device_ip else [],
            "organization": None,
            "offlineOnlyWhenMissedHeartbeats": True,
            "createdAt": now,
            "updatedAt": now,
        }
        if user_id is not None:
            device_doc["userId"] = user_id
            device_doc["user_id"] = user_id
        if family_id is not None:
            device_doc["family_id"] = family_id
        if owner_id_val is not None:
            device_doc["owner_id"] = owner_id_val
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

    # Update existing device: status and lastSeen
    # When device has offlineOnlyWhenMissedHeartbeats, never set offline from payload – only
    # the sweep can mark offline when heartbeats stop. Use for doorbells/cameras that don't
    # respond to port checks.
    offline_only_when_missed = device.get("offlineOnlyWhenMissedHeartbeats", False)
    if offline_only_when_missed:
        # Any received heartbeat = online; sweep will set offline if heartbeats stop
        update_set_status = "online"
    else:
        # When agent reports "offline", short grace then flip (security: detect issues quickly).
        heartbeat_interval = int(device.get("heartbeatInterval", 30))
        grace_sec = max(30, min(90, heartbeat_interval * 2))
        if payload.status == "offline" and device.get("status") == "online":
            last_seen = device.get("lastSeen")
            if last_seen:
                try:
                    age = (now - last_seen).total_seconds()
                except TypeError:
                    age = 999
                if age < grace_sec:
                    update_set_status = "online"
                else:
                    update_set_status = "offline"
            else:
                update_set_status = "offline"
        else:
            update_set_status = payload.status

    update_set: Dict[str, Any] = {
        "status": update_set_status,
        "lastSeen": now,
        "updatedAt": now,
    }

    if payload.signal_strength is not None:
        update_set["signalStrength"] = payload.signal_strength

    update_ops: Dict[str, Any] = {"$set": update_set}

    # Only accept device IP updates when the reported IP is not a router/gateway (avoids false "IP changed to router" alerts)
    device_owner_id = device.get("userId") or device.get("user_id")
    new_ip = payload.ip_address
    reject_ip = (
        not new_ip
        or _is_likely_router_ip(new_ip)
        or await _is_user_router_ip(db, device_owner_id, new_ip)
    )
    if new_ip and new_ip != device.get("ipAddress") and not reject_ip:
        update_set["ipAddress"] = new_ip
        update_ops["$push"] = {"ipAddressHistory": new_ip}

        # Check for suspicious IP change
        from services.security_monitor import get_security_monitor
        security_monitor = get_security_monitor()
        anomaly = await security_monitor.check_ip_change_anomaly(
            db,
            str(device["_id"]),
            new_ip,
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
        update_set["owner_id"] = family_id_obj if family_id_obj is not None else user_id_obj
    if family_id_obj is not None and device.get("family_id") is None:
        update_set["family_id"] = family_id_obj
        update_set["owner_id"] = family_id_obj

    # Backfill owner_id on legacy documents (matches compound unique index namespace)
    if device.get("owner_id") is None and "owner_id" not in update_set:
        inferred = device.get("family_id") or device.get("userId") or device.get("user_id")
        if inferred is not None:
            update_set["owner_id"] = inferred

    await db.devices.update_one({"_id": device["_id"]}, update_ops)

    # When device reports online, resolve any stale "device is offline" alerts so the dashboard stays accurate
    if payload.status == "online":
        from services.device_status_monitor import resolve_offline_alerts_for_device
        await resolve_offline_alerts_for_device(device["_id"])

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

