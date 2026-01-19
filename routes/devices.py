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


async def _get_user_family_id(user_id: ObjectId, db) -> Optional[ObjectId]:
    """Get user's family ID if they're part of one"""
    membership = await db.family_members.find_one({"user_id": user_id})
    return membership["family_id"] if membership else None


async def _can_manage_devices(user_id: ObjectId, db) -> bool:
    """Check if user can manage devices (always true for device owner, check permission for family members)"""
    membership = await db.family_members.find_one({"user_id": user_id})
    if not membership:
        return True  # Not in family, full control
    return membership.get("can_manage_devices", True)

@router.get("/", response_model=DeviceListResponse)
async def get_devices(
    type: Optional[str] = Query(None, description="Filter by device type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    user: dict = Depends(get_current_user)
):
    """
    Get all devices with optional filters and pagination
    Shows devices owned by user OR their family
    
    Query params:
    - type: Filter by device type (Camera, Router, etc.)
    - status: Filter by status (online, offline, error)
    - name: Filter by name (case-insensitive partial match)
    - page: Page number (default 1)
    - limit: Items per page (default 10, max 100)
    """
    try:
        db = await get_database()
    
    # Build filter - show user's devices OR family devices
    family_id = await _get_user_family_id(user["_id"], db)
    
    # Start with user/family filter
    if family_id:
        # Show all family devices
        filter_query = {"family_id": family_id}
    else:
        # Show only user's devices (check both user_id and userId for compatibility)
        # Use simpler approach - try userId first (most common)
        filter_query = {"userId": user["_id"]}
    
    # Add additional filters directly
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
    
    # If no devices found and we're using userId, try user_id as fallback
    if len(devices_raw) == 0 and not family_id and "userId" in filter_query:
        # Try with user_id instead
        fallback_query = filter_query.copy()
        fallback_query["user_id"] = fallback_query.pop("userId")
        cursor = db.devices.find(fallback_query).skip(skip).limit(limit).sort([("status", 1), ("lastSeen", -1)])
        devices_raw = await cursor.to_list(length=limit)
        if len(devices_raw) > 0:
            filter_query = fallback_query
    
    # Get total count
    total = await db.devices.count_documents(filter_query)
    
    # Shape response
    devices = []
    for d in devices_raw:
        try:
            # Handle both createdAt/created_at and updatedAt/updated_at
            created_at = d.get("createdAt") or d.get("created_at") or datetime.utcnow()
            updated_at = d.get("updatedAt") or d.get("updated_at") or datetime.utcnow()
            
            devices.append(DeviceResponse(
                id=str(d["_id"]),
                device_id=d.get("deviceId", d.get("device_id", "")),
                name=d.get("name", ""),
                type=d.get("type", ""),
                ip_address=d.get("ipAddress", d.get("ip_address", "")),
                status=d.get("status", "offline"),
                last_seen=d.get("lastSeen") or d.get("last_seen"),
                heartbeat_interval=d.get("heartbeatInterval", d.get("heartbeat_interval", 30)),
                alerts_enabled=d.get("alertsEnabled", d.get("alerts_enabled", True)),
                signal_strength=d.get("signalStrength") or d.get("signal_strength"),
                ip_address_history=d.get("ipAddressHistory", d.get("ip_address_history", [])),
                organization=str(d["organization"]) if d.get("organization") else None,
                created_at=created_at,
                updated_at=updated_at
            ))
        except Exception as e:
            print(f"[ERROR] Failed to parse device {d.get('_id')}: {e}")
            continue
    
    return DeviceListResponse(
        page=page,
        total=total,
        devices=devices
    )
    except Exception as e:
        import traceback
        print(f"[ERROR] get_devices failed: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load devices: {str(e)}"
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
    - Associates device with user or their family
    """
    db = await get_database()
    
    # Check if user can manage devices
    can_manage = await _can_manage_devices(user["_id"], db)
    if not can_manage:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create devices"
        )
    
    # Check plan device limit
    await PlanLimits.check_device_limit(user)
    
    # Get family ID if user is in a family
    family_id = await _get_user_family_id(user["_id"], db)
    
    # Check if device_id already exists for this user/family
    filter_existing = {"deviceId": device.device_id}
    if family_id:
        filter_existing["family_id"] = family_id
    else:
        filter_existing["user_id"] = user["_id"]
    
    existing = await db.devices.find_one(filter_existing)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device with ID '{device.device_id}' already exists"
        )
    
    # Check if IP already exists for this user/family
    filter_ip = {"ipAddress": device.ip_address}
    if family_id:
        filter_ip["family_id"] = family_id
    else:
        filter_ip["user_id"] = user["_id"]
        
    existing_ip = await db.devices.find_one(filter_ip)
    if existing_ip:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device with IP '{device.ip_address}' already exists"
        )
    
    # Create device document
    device_doc = {
        "user_id": user["_id"],  # Creator
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
    
    # Add family_id if user is in a family
    if family_id:
        device_doc["family_id"] = family_id
    
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