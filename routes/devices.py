# routes/devices.py - Device Management Routes
from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from typing import Optional
from bson import ObjectId
from datetime import datetime

from models import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse
from database import get_database
from routes.auth import get_current_user
from middleware.plan_limits import PlanLimits
from services.audit_logger import AuditLogger

router = APIRouter()


async def _get_user_family_id(user_id: ObjectId, db) -> Optional[ObjectId]:
    """Get user's family ID if they're part of one"""
    try:
        membership = await db.family_members.find_one({"user_id": user_id})
        if membership and "family_id" in membership:
            return membership["family_id"]
        return None
    except Exception as e:
        print(f"[ERROR] _get_user_family_id failed: {e}")
        return None


async def _can_manage_devices(user_id: ObjectId, db) -> bool:
    """Check if user can manage devices (always true for device owner, check permission for family members)"""
    membership = await db.family_members.find_one({"user_id": user_id})
    if not membership:
        return True  # Not in family, full control
    return membership.get("can_manage_devices", True)

@router.get("/", response_model=DeviceListResponse)
async def get_devices(
    device_type: Optional[str] = Query(None, alias="type", description="Filter by device type"),
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
        
        # Ensure user_id is ObjectId
        user_id = user["_id"]
        if not isinstance(user_id, ObjectId):
            user_id = ObjectId(user_id)
        
        # Build filter - show user's devices OR family devices
        family_id = await _get_user_family_id(user_id, db)
        
        # Start with user/family filter
        if family_id:
            # Show all family devices
            filter_query = {"family_id": family_id}
        else:
            # Show only user's devices (check both user_id and userId for compatibility)
            # Use simpler approach - try userId first (most common)
            filter_query = {"userId": user_id}
        
        # Exclude soft-deleted devices
        filter_query["isDeleted"] = {"$ne": True}

        # Add additional filters directly
        if device_type:
            filter_query["type"] = device_type
        if status:
            filter_query["status"] = status
        if name:
            filter_query["$or"] = [
                {"name": {"$regex": name, "$options": "i"}},
                {"deviceId": {"$regex": name, "$options": "i"}}
            ]
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get devices - sort by status first, then by lastSeen (if exists), then by _id
        try:
            cursor = db.devices.find(filter_query).skip(skip).limit(limit).sort([("status", 1), ("lastSeen", -1), ("_id", -1)])
            devices_raw = await cursor.to_list(length=limit)
        except Exception as e:
            print(f"[ERROR] Failed to query devices: {e}")
            # Try without sort as fallback
            try:
                cursor = db.devices.find(filter_query).skip(skip).limit(limit)
                devices_raw = await cursor.to_list(length=limit)
            except Exception as e2:
                print(f"[ERROR] Failed to query devices (no sort): {e2}")
                devices_raw = []
        
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
        try:
            total = await db.devices.count_documents(filter_query)
        except Exception as e:
            print(f"[ERROR] Failed to count devices: {e}")
            total = len(devices_raw)
        
        # Shape response
        devices = []
        for d in devices_raw:
            try:
                # Handle both createdAt/created_at and updatedAt/updated_at
                created_at = d.get("createdAt") or d.get("created_at") or datetime.utcnow()
                updated_at = d.get("updatedAt") or d.get("updated_at") or datetime.utcnow()
                
                # Get groups (convert ObjectIds to strings)
                groups = d.get("groups", [])
                groups_list = [str(g) if hasattr(g, '__str__') else g for g in groups] if groups else []
                
                devices.append(DeviceResponse(
                id=str(d["_id"]),
                device_id=d.get("deviceId", d.get("device_id", "")),
                name=d.get("name", ""),
                type=d.get("type", ""),
                router_ip=d.get("routerIp") or d.get("router_ip"),
                device_ip=d.get("ipAddress", d.get("ip_address", "")),
                ip_address=d.get("ipAddress", d.get("ip_address", "")),  # Backward compatibility
                status=d.get("status", "offline"),
                last_seen=d.get("lastSeen") or d.get("last_seen"),
                heartbeat_interval=d.get("heartbeatInterval", d.get("heartbeat_interval", 30)),
                alerts_enabled=d.get("alertsEnabled", d.get("alerts_enabled", True)),
                signal_strength=d.get("signalStrength") or d.get("signal_strength"),
                ip_address_history=d.get("ipAddressHistory", d.get("ip_address_history", [])),
                organization=str(d["organization"]) if d.get("organization") else None,
                groups=groups_list,
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
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] get_devices failed: {e}")
        print(error_trace)
        # Log to console with full traceback
        import sys
        print("=" * 60, file=sys.stderr)
        print(f"ERROR in get_devices: {type(e).__name__}: {e}", file=sys.stderr)
        print(error_trace, file=sys.stderr)
        print("=" * 60, file=sys.stderr)
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
    
    device = await db.devices.find_one({"deviceId": device_id, "isDeleted": {"$ne": True}})
    
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
            "router_ip": device.get("routerIp") or device.get("router_ip"),
            "device_ip": device.get("ipAddress"),
            "ip_address": device.get("ipAddress"),  # Backward compatibility
            "status": device.get("status"),
            "last_seen": device.get("lastSeen"),
            "signal_strength": device.get("signalStrength"),
            "heartbeat_interval": device.get("heartbeatInterval"),
            "alerts_enabled": device.get("alertsEnabled"),
            "ip_address_history": device.get("ipAddressHistory", [])
        }
    }

@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(device: DeviceCreate, user: dict = Depends(get_current_user), request: Request = None):
    """
    Register a new device
    
    - Checks plan device limits
    - Validates device doesn't already exist
    - Verifies device is on the same network (if router IP configured)
    - Associates device with user or their family
    """
    db = await get_database()
    
    # Get router IP from network settings if not provided
    settings = await db.network_settings.find_one({"userId": user["_id"]})
    router_ip = device.router_ip
    if not router_ip and settings:
        router_ip = settings.get("routerIp")
    
    if not router_ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Router IP is required. Please configure it in settings first."
        )
    
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
    
    # Ensure user_id is ObjectId
    user_id = user["_id"]
    if not isinstance(user_id, ObjectId):
        user_id = ObjectId(user_id)
    
    # Check if device_id already exists for this user/family
    if family_id:
        filter_existing = {"deviceId": device.device_id, "family_id": family_id}
    else:
        # Check both userId and user_id for compatibility
        filter_existing = {
            "deviceId": device.device_id,
            "$or": [
                {"userId": user_id},
                {"user_id": user_id}
            ]
        }
    
    existing = await db.devices.find_one(filter_existing)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device with ID '{device.device_id}' already exists"
        )
    
    # REMOVED: IP uniqueness check - allow multiple devices with same router IP
    
    # Create device document
    device_doc = {
        "userId": user_id,  # Creator (use camelCase for consistency)
        "user_id": user_id,  # Also store snake_case for compatibility
        "deviceId": device.device_id,
        "name": device.name,
        "type": device.type,
        "routerIp": router_ip,
        "ipAddress": device.device_ip or "0.0.0.0",  # Optional device IP
        "status": "offline",
        "lastSeen": datetime.utcnow(),
        "heartbeatInterval": device.heartbeat_interval,
        "alertsEnabled": device.alerts_enabled,
        "signalStrength": None,
        "ipAddressHistory": [device.device_ip] if device.device_ip else [],
        "organization": ObjectId(device.organization) if device.organization else None,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "isDeleted": False,
        "deletedAt": None
    }
    
    # Add family_id if user is in a family
    if family_id:
        device_doc["family_id"] = family_id
    
    result = await db.devices.insert_one(device_doc)

    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None

    await AuditLogger.log_device_created(
        db=db,
        user_id=user_id,
        user_email=user.get("email", ""),
        user_name=user.get("name", ""),
        device_id=device.device_id,
        device_name=device.name,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # Get groups (convert ObjectIds to strings)
    groups = device_doc.get("groups", [])
    groups_list = [str(g) if hasattr(g, '__str__') else g for g in groups] if groups else []
    
    return DeviceResponse(
        id=str(result.inserted_id),
        device_id=device.device_id,
        name=device.name,
        type=device.type,
        router_ip=router_ip,
        device_ip=device.device_ip or "0.0.0.0",
        ip_address=device.device_ip or "0.0.0.0",  # Backward compatibility
        status="offline",
        last_seen=device_doc["lastSeen"],
        heartbeat_interval=device.heartbeat_interval,
        alerts_enabled=device.alerts_enabled,
        signal_strength=None,
        ip_address_history=[device.device_ip] if device.device_ip else [],
        organization=device.organization,
        groups=groups_list,
        created_at=device_doc["createdAt"],
        updated_at=device_doc["updatedAt"]
    )

@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: str, updates: DeviceUpdate, user: dict = Depends(get_current_user), request: Request = None):
    """
    Update device information
    """
    db = await get_database()

    # Check if user can manage devices
    can_manage = await _can_manage_devices(user["_id"], db)
    if not can_manage:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update devices"
        )

    # Ensure user_id is ObjectId
    user_id = user["_id"]
    if not isinstance(user_id, ObjectId):
        user_id = ObjectId(user_id)

    # Get family ID if user is in a family
    family_id = await _get_user_family_id(user_id, db)
    if family_id:
        filter_query = {"deviceId": device_id, "family_id": family_id, "isDeleted": {"$ne": True}}
    else:
        filter_query = {
            "deviceId": device_id,
            "isDeleted": {"$ne": True},
            "$or": [
                {"userId": user_id},
                {"user_id": user_id}
            ]
        }
    
    # Find device
    device = await db.devices.find_one(filter_query)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Build update document
    update_doc = {"updatedAt": datetime.utcnow()}
    
    changes = {}

    if updates.name is not None:
        update_doc["name"] = updates.name
        changes["name"] = updates.name
    if updates.type is not None:
        update_doc["type"] = updates.type
        changes["type"] = updates.type
    if updates.router_ip is not None:
        update_doc["routerIp"] = updates.router_ip
        changes["router_ip"] = updates.router_ip
    if updates.heartbeat_interval is not None:
        update_doc["heartbeatInterval"] = updates.heartbeat_interval
        changes["heartbeat_interval"] = updates.heartbeat_interval
    if updates.device_ip is not None or updates.ip_address is not None:
        new_ip = updates.device_ip if updates.device_ip is not None else updates.ip_address
        update_doc["ipAddress"] = new_ip
        changes["device_ip"] = new_ip
        # Add to history if changed
        if new_ip != device.get("ipAddress"):
            update_doc["$push"] = {"ipAddressHistory": new_ip}
    if updates.status is not None:
        update_doc["status"] = updates.status
        changes["status"] = updates.status
    if updates.signal_strength is not None:
        update_doc["signalStrength"] = updates.signal_strength
        changes["signal_strength"] = updates.signal_strength
    if updates.alerts_enabled is not None:
        update_doc["alertsEnabled"] = updates.alerts_enabled
        changes["alerts_enabled"] = updates.alerts_enabled
    
    # Update device
    update_payload = {"$set": update_doc}
    if "$push" in update_doc:
        update_payload["$push"] = update_doc.pop("$push")

    await db.devices.update_one(filter_query, update_payload)

    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None

    await AuditLogger.log_device_updated(
        db=db,
        user_id=user_id,
        user_email=user.get("email", ""),
        user_name=user.get("name", ""),
        device_id=device_id,
        device_name=update_doc.get("name", device.get("name", "")),
        changes=changes,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # Get updated device
    updated_device = await db.devices.find_one(filter_query)
    
    # Get groups (convert ObjectIds to strings)
    groups = updated_device.get("groups", [])
    groups_list = [str(g) if hasattr(g, '__str__') else g for g in groups] if groups else []
    
    return DeviceResponse(
        id=str(updated_device["_id"]),
        device_id=updated_device["deviceId"],
        name=updated_device["name"],
        type=updated_device["type"],
        router_ip=updated_device.get("routerIp") or updated_device.get("router_ip"),
        device_ip=updated_device.get("ipAddress", ""),
        ip_address=updated_device.get("ipAddress", ""),  # Backward compatibility
        status=updated_device["status"],
        last_seen=updated_device.get("lastSeen"),
        heartbeat_interval=updated_device["heartbeatInterval"],
        alerts_enabled=updated_device["alertsEnabled"],
        signal_strength=updated_device.get("signalStrength"),
        ip_address_history=updated_device.get("ipAddressHistory", []),
        organization=str(updated_device["organization"]) if updated_device.get("organization") else None,
        groups=groups_list,
        created_at=updated_device.get("createdAt", datetime.utcnow()),
        updated_at=updated_device["updatedAt"]
    )

@router.delete("/{device_id}")
async def delete_device(device_id: str, user: dict = Depends(get_current_user), request: Request = None):
    """
    Delete a device
    """
    db = await get_database()

    # Check if user can manage devices
    can_manage = await _can_manage_devices(user["_id"], db)
    if not can_manage:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete devices"
        )

    # Ensure user_id is ObjectId
    user_id = user["_id"]
    if not isinstance(user_id, ObjectId):
        user_id = ObjectId(user_id)

    # Get family ID if user is in a family
    family_id = await _get_user_family_id(user_id, db)
    if family_id:
        filter_query = {"deviceId": device_id, "family_id": family_id, "isDeleted": {"$ne": True}}
    else:
        filter_query = {
            "deviceId": device_id,
            "isDeleted": {"$ne": True},
            "$or": [
                {"userId": user_id},
                {"user_id": user_id}
            ]
        }

    device = await db.devices.find_one(filter_query)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    await db.devices.update_one(
        filter_query,
        {"$set": {"isDeleted": True, "deletedAt": datetime.utcnow(), "updatedAt": datetime.utcnow()}}
    )

    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None

    await AuditLogger.log_device_deleted(
        db=db,
        user_id=user_id,
        user_email=user.get("email", ""),
        user_name=user.get("name", ""),
        device_id=device_id,
        device_name=device.get("name", ""),
        ip_address=client_ip,
        user_agent=user_agent
    )

    return {"message": f"Device '{device_id}' deleted successfully"}