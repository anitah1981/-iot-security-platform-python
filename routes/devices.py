# routes/devices.py - Device Management Routes
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional
from bson import ObjectId
from datetime import datetime

from models import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse
from database import get_database
from routes.auth import get_current_user
from middleware.plan_limits import PlanLimits

router = APIRouter()

@router.get("/", response_model=DeviceListResponse)
async def get_devices(
    type: Optional[str] = Query(None, description="Filter by device type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Get all devices with optional filters and pagination
    
    Query params:
    - type: Filter by device type (Camera, Router, etc.)
    - status: Filter by status (online, offline, error)
    - name: Filter by name (case-insensitive partial match)
    - page: Page number (default 1)
    - limit: Items per page (default 10, max 100)
    """
    db = await get_database()
    
    # Build filter
    filter_query = {}
    if type:
        filter_query["type"] = type
    if status:
        filter_query["status"] = status
    if name:
        filter_query["name"] = {"$regex": name, "$options": "i"}
    
    # Calculate skip
    skip = (page - 1) * limit
    
    # Get devices
    cursor = db.devices.find(filter_query).skip(skip).limit(limit).sort([("status", 1), ("lastSeen", -1)])
    devices_raw = await cursor.to_list(length=limit)
    
    # Get total count
    total = await db.devices.count_documents(filter_query)
    
    # Shape response
    devices = []
    for d in devices_raw:
        devices.append(DeviceResponse(
            id=str(d["_id"]),
            device_id=d.get("deviceId", ""),
            name=d.get("name", ""),
            type=d.get("type", ""),
            ip_address=d.get("ipAddress", ""),
            status=d.get("status", "offline"),
            last_seen=d.get("lastSeen"),
            heartbeat_interval=d.get("heartbeatInterval", 30),
            alerts_enabled=d.get("alertsEnabled", True),
            signal_strength=d.get("signalStrength"),
            ip_address_history=d.get("ipAddressHistory", []),
            organization=str(d["organization"]) if d.get("organization") else None,
            created_at=d.get("createdAt", datetime.utcnow()),
            updated_at=d.get("updatedAt", datetime.utcnow())
        ))
    
    return DeviceListResponse(
        page=page,
        total=total,
        devices=devices
    )

@router.get("/{device_id}/status")
async def get_device_status(device_id: str):
    """
    Get live status/details for a single device
    
    Use logical device_id (like 'dev-001')
    """
    db = await get_database()
    
    device = await db.devices.find_one({"deviceId": device_id})
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return {
        "device": {
            "device_id": device.get("deviceId"),
            "name": device.get("name"),
            "type": device.get("type"),
            "ip_address": device.get("ipAddress"),
            "status": device.get("status"),
            "last_seen": device.get("lastSeen"),
            "signal_strength": device.get("signalStrength"),
            "heartbeat_interval": device.get("heartbeatInterval"),
            "alerts_enabled": device.get("alertsEnabled"),
            "ip_address_history": device.get("ipAddressHistory", [])
        }
    }

@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(device: DeviceCreate, user: dict = Depends(get_current_user)):
    """
    Register a new device
    
    - Checks plan device limits
    - Validates device doesn't already exist
    - Associates device with user
    """
    db = await get_database()
    
    # Check plan device limit
    await PlanLimits.check_device_limit(user)
    
    # Check if device_id already exists for this user
    existing = await db.devices.find_one({
        "deviceId": device.device_id,
        "userId": user["_id"]
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device with ID '{device.device_id}' already exists"
        )
    
    # Check if IP already exists for this user
    existing_ip = await db.devices.find_one({
        "ipAddress": device.ip_address,
        "userId": user["_id"]
    })
    if existing_ip:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device with IP '{device.ip_address}' already exists"
        )
    
    # Create device document
    device_doc = {
        "userId": user["_id"],  # Associate device with user
        "deviceId": device.device_id,
        "name": device.name,
        "type": device.type,
        "ipAddress": device.ip_address,
        "status": "offline",
        "lastSeen": datetime.utcnow(),
        "heartbeatInterval": device.heartbeat_interval,
        "alertsEnabled": device.alerts_enabled,
        "signalStrength": None,
        "ipAddressHistory": [device.ip_address],
        "organization": ObjectId(device.organization) if device.organization else None,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    result = await db.devices.insert_one(device_doc)
    
    return DeviceResponse(
        id=str(result.inserted_id),
        device_id=device.device_id,
        name=device.name,
        type=device.type,
        ip_address=device.ip_address,
        status="offline",
        last_seen=device_doc["lastSeen"],
        heartbeat_interval=device.heartbeat_interval,
        alerts_enabled=device.alerts_enabled,
        signal_strength=None,
        ip_address_history=[device.ip_address],
        organization=device.organization,
        created_at=device_doc["createdAt"],
        updated_at=device_doc["updatedAt"]
    )

@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: str, updates: DeviceUpdate):
    """
    Update device information
    """
    db = await get_database()
    
    # Find device
    device = await db.devices.find_one({"deviceId": device_id})
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Build update document
    update_doc = {"updatedAt": datetime.utcnow()}
    
    if updates.name is not None:
        update_doc["name"] = updates.name
    if updates.ip_address is not None:
        update_doc["ipAddress"] = updates.ip_address
        # Add to history if changed
        if updates.ip_address != device.get("ipAddress"):
            update_doc["$push"] = {"ipAddressHistory": updates.ip_address}
    if updates.status is not None:
        update_doc["status"] = updates.status
    if updates.signal_strength is not None:
        update_doc["signalStrength"] = updates.signal_strength
    if updates.alerts_enabled is not None:
        update_doc["alertsEnabled"] = updates.alerts_enabled
    
    # Update device
    await db.devices.update_one(
        {"deviceId": device_id},
        {"$set": update_doc}
    )
    
    # Get updated device
    updated_device = await db.devices.find_one({"deviceId": device_id})
    
    return DeviceResponse(
        id=str(updated_device["_id"]),
        device_id=updated_device["deviceId"],
        name=updated_device["name"],
        type=updated_device["type"],
        ip_address=updated_device["ipAddress"],
        status=updated_device["status"],
        last_seen=updated_device.get("lastSeen"),
        heartbeat_interval=updated_device["heartbeatInterval"],
        alerts_enabled=updated_device["alertsEnabled"],
        signal_strength=updated_device.get("signalStrength"),
        ip_address_history=updated_device.get("ipAddressHistory", []),
        organization=str(updated_device["organization"]) if updated_device.get("organization") else None,
        created_at=updated_device.get("createdAt", datetime.utcnow()),
        updated_at=updated_device["updatedAt"]
    )

@router.delete("/{device_id}")
async def delete_device(device_id: str):
    """
    Delete a device
    """
    db = await get_database()
    
    result = await db.devices.delete_one({"deviceId": device_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return {"message": f"Device '{device_id}' deleted successfully"}