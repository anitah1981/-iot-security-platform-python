# routes/alerts.py - Alert Management Routes
from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks, Depends
from typing import Optional, List
from bson import ObjectId
from datetime import datetime, timedelta

from models import AlertCreate, AlertResponse, AlertListResponse
from database import get_database
from routes.auth import get_current_user
from routes.devices import _get_user_family_id

from pydantic import BaseModel, Field

router = APIRouter()


async def _device_ids_for_user_alerts(db, user_id: ObjectId) -> list[ObjectId]:
    """Devices whose alerts this user may see (solo + family), matching device list semantics."""
    family_id = await _get_user_family_id(user_id, db)
    if family_id:
        q = {
            "$or": [
                {"userId": user_id},
                {"user_id": user_id},
                {"family_id": family_id},
            ],
            "isDeleted": {"$ne": True},
        }
    else:
        q = {
            "$or": [{"userId": user_id}, {"user_id": user_id}],
            "isDeleted": {"$ne": True},
        }
    devs = await db.devices.find(q).to_list(length=1000)
    return [ObjectId(d["_id"]) for d in devs]


async def _alert_document_to_response(db, a: dict) -> AlertResponse:
    alert_device_id = a.get("deviceId") or a.get("device_id")
    device_info = None
    if alert_device_id:
        try:
            oid = (
                alert_device_id
                if isinstance(alert_device_id, ObjectId)
                else ObjectId(str(alert_device_id))
            )
            dev = await db.devices.find_one({"_id": oid})
            if dev:
                device_info = {
                    "id": str(dev["_id"]),
                    "logical_id": dev.get("deviceId") or dev.get("device_id"),
                    "name": dev.get("name"),
                    "type": dev.get("type"),
                }
        except Exception:
            pass
    created_at = a.get("createdAt") or a.get("created_at") or datetime.utcnow()
    resolved_at = a.get("resolvedAt") or a.get("resolved_at")
    return AlertResponse(
        id=str(a["_id"]),
        device_id=str(alert_device_id) if alert_device_id else "",
        message=a.get("message", ""),
        severity=a.get("severity", "medium"),
        type=a.get("type", "system"),
        context=a.get("context", {}),
        resolved=a.get("resolved", False),
        resolved_at=resolved_at,
        created_at=created_at,
        device=device_info,
    )

async def send_alert_notifications(alert_id: str, device_id: str, alert_message: str, alert_severity: str):
    """Background task to send notifications for an alert"""
    try:
        from services.notification_service import send_alert_notification
        
        db = await get_database()
        
        # Get device info
        device = await db.devices.find_one({"_id": ObjectId(device_id)})
        if not device:
            print(f"Device {device_id} not found for alert {alert_id}")
            return
        
        device_name = device.get("name", "Unknown Device")
        
        # For MVP: Send notifications to all users (since devices aren't user-linked yet)
        # In production, you'd link devices to users
        users = await db.users.find().to_list(length=100)
        
        for user in users:
            user_id = str(user["_id"])
            
            # Get user's notification preferences
            prefs = await db.notification_preferences.find_one({"userId": ObjectId(user_id)})
            
            if not prefs:
                # Use default preferences
                prefs = {
                    "emailEnabled": True,
                    "smsEnabled": False,
                    "whatsappEnabled": False,
                    "voiceEnabled": False,
                    "emailSeverities": ["low", "medium", "high", "critical"],
                    "smsSeverities": ["high", "critical"],
                    "whatsappSeverities": ["medium", "high", "critical"],
                    "voiceSeverities": ["critical"],
                }
            
            # Send notifications
            results = await send_alert_notification(
                user_email=user.get("email", ""),
                user_name=user.get("name", "User"),
                device_name=device_name,
                alert_message=alert_message,
                alert_severity=alert_severity,
                notification_prefs=prefs
            )
            
            # Log results
            for result in results:
                print(f"Notification {result.channel} to {user.get('email')}: {result.detail}")
                
    except Exception as e:
        print(f"Error sending alert notifications: {e}")

@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(alert: AlertCreate, background_tasks: BackgroundTasks):
    """
    Create an alert (manual or auto from monitoring)
    
    Deduplication rules by type:
    - power: Only 1 alert (no duplicates ever)
    - connectivity: Deduped within 5 minutes
    - system: Deduped within 10 minutes
    - security: Multiple alerts allowed (every event matters)
    """
    db = await get_database()
    
    # Deduplication logic
    allow_duplicate = True
    time_window = None
    
    if alert.type == "power":
        # Power cuts are one-off - don't allow duplicates at all
        allow_duplicate = False
        time_window = None
    elif alert.type == "connectivity":
        # Device going offline/online - allow new alert only if 5 minutes passed
        allow_duplicate = False
        time_window = 5 * 60  # 5 minutes in seconds
    elif alert.type == "system":
        # System issues - only once every 10 mins
        allow_duplicate = False
        time_window = 10 * 60  # 10 minutes in seconds
    elif alert.type == "security":
        # Security events - allow duplicates (every event matters)
        allow_duplicate = True
    
    # Check for recent duplicate if duplicates not allowed
    # Note: We check deviceId since new alerts are created with deviceId
    if not allow_duplicate:
        base_query = {
            "deviceId": ObjectId(alert.device_id),
            "message": alert.message,
            "type": alert.type,
            "severity": alert.severity
        }
        
        if time_window:
            cutoff = datetime.utcnow() - timedelta(seconds=time_window)
            # Check both createdAt and created_at for backward compatibility
            query = {
                **base_query,
                "$or": [
                    {"createdAt": {"$gte": cutoff}},
                    {"created_at": {"$gte": cutoff}}
                ]
            }
        else:
            query = base_query
        
        existing_alert = await db.alerts.find_one(query)
        
        if existing_alert:
            # Handle both deviceId and device_id formats
            existing_device_id = existing_alert.get("deviceId") or existing_alert.get("device_id")
            created_at = existing_alert.get("createdAt") or existing_alert.get("created_at") or datetime.utcnow()
            return AlertResponse(
                id=str(existing_alert["_id"]),
                device_id=str(existing_device_id) if existing_device_id else "",
                message=existing_alert.get("message", ""),
                severity=existing_alert.get("severity", "medium"),
                type=existing_alert.get("type", "system"),
                context=existing_alert.get("context", {}),
                resolved=existing_alert.get("resolved", False),
                resolved_at=existing_alert.get("resolvedAt") or existing_alert.get("resolved_at"),
                created_at=created_at
            )
    
    # Create new alert
    alert_doc = {
        "deviceId": ObjectId(alert.device_id),
        "message": alert.message,
        "severity": alert.severity,
        "type": alert.type,
        "context": alert.context or {},
        "resolved": False,
        "resolvedAt": None,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    result = await db.alerts.insert_one(alert_doc)
    alert_id = str(result.inserted_id)
    
    # Queue background notification task
    background_tasks.add_task(
        send_alert_notifications,
        alert_id=alert_id,
        device_id=alert.device_id,
        alert_message=alert.message,
        alert_severity=alert.severity
    )
    
    return AlertResponse(
        id=alert_id,
        device_id=alert.device_id,
        message=alert.message,
        severity=alert.severity,
        type=alert.type,
        context=alert.context or {},
        resolved=False,
        resolved_at=None,
        created_at=alert_doc["createdAt"]
    )

@router.get("", response_model=AlertListResponse)
async def get_alerts(
    device_id: Optional[str] = Query(None, description="Filter by device MongoDB ObjectId"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    type: Optional[str] = Query(None, description="Filter by alert type"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status (True/False). If not specified, returns all alerts"),
    since: Optional[datetime] = Query(None, description="Only alerts after this timestamp"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    user: dict = Depends(get_current_user)
):
    """
    Get alerts with filters and pagination - OPTIMIZED for performance
    Only returns alerts for the current user's devices
    """
    db = await get_database()
    user_id = user["_id"]
    if not isinstance(user_id, ObjectId):
        user_id = ObjectId(user_id)
    
    # Device IDs for this user (includes family-shared devices)
    user_device_ids = await _device_ids_for_user_alerts(db, user_id)
    
    if not user_device_ids:
        return AlertListResponse(page=page, total=0, alerts=[])
    
    # Build filter - only alerts for user's devices
    filter_query = {
        "$or": [
            {"deviceId": {"$in": user_device_ids}},
            {"device_id": {"$in": user_device_ids}}
        ]
    }
    
    # Device filter - check both field names
    if device_id:
        device_obj_id = ObjectId(device_id)
        # Verify device belongs to user
        if device_obj_id not in user_device_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device not found or access denied")
        filter_query["$or"] = [
            {"deviceId": device_obj_id},
            {"device_id": device_obj_id}
        ]
    
    # Date filter - check both field names
    if since:
        date_condition = {
            "$or": [
                {"createdAt": {"$gte": since}},
                {"created_at": {"$gte": since}}
            ]
        }
        # Combine with existing $or
        if "$or" in filter_query and isinstance(filter_query["$or"], list) and len(filter_query["$or"]) > 0:
            device_condition = {"$or": filter_query.pop("$or")}
            filter_query["$and"] = [device_condition, date_condition]
        else:
            filter_query.update(date_condition)
    
    # Add direct field filters (these are AND conditions)
    if severity:
        filter_query["severity"] = severity
    if type:
        filter_query["type"] = type
    if resolved is not None:
        filter_query["resolved"] = resolved
    
    # Calculate skip
    skip = (page - 1) * limit
    
    # Get alerts
    cursor = db.alerts.find(filter_query).sort("createdAt", -1).skip(skip).limit(limit)
    alerts_raw = await cursor.to_list(length=limit)
    
    # Get total count
    try:
        total = await db.alerts.count_documents(filter_query)
    except Exception:
        total = len(alerts_raw) if len(alerts_raw) == limit else len(alerts_raw)
    
    # Fetch all devices in one query
    device_ids_in_alerts = []
    for a in alerts_raw:
        alert_device_id = a.get("deviceId") or a.get("device_id")
        if alert_device_id:
            try:
                device_ids_in_alerts.append(ObjectId(alert_device_id))
            except:
                pass
    
    # Single query to get all devices
    devices_map = {}
    if device_ids_in_alerts:
        devices_cursor = db.devices.find({"_id": {"$in": device_ids_in_alerts}})
        devices_list = await devices_cursor.to_list(length=len(device_ids_in_alerts))
        for device in devices_list:
            devices_map[str(device["_id"])] = {
                "id": str(device["_id"]),
                "logical_id": device.get("deviceId") or device.get("device_id"),
                "name": device.get("name"),
                "type": device.get("type")
            }
    
    # Shape response with device info (now using pre-fetched map)
    alerts = []
    for a in alerts_raw:
        # Get device ID - handle both deviceId and device_id formats
        alert_device_id = a.get("deviceId") or a.get("device_id")
        
        # Get device info from pre-fetched map (no database query!)
        device_info = devices_map.get(str(alert_device_id)) if alert_device_id else None
        
        # Handle both createdAt and created_at
        created_at = a.get("createdAt") or a.get("created_at") or datetime.utcnow()
        resolved_at = a.get("resolvedAt") or a.get("resolved_at")
        
        alerts.append(AlertResponse(
            id=str(a["_id"]),
            device_id=str(alert_device_id) if alert_device_id else "",
            message=a.get("message", ""),
            severity=a.get("severity", "medium"),
            type=a.get("type", "system"),
            context=a.get("context", {}),
            resolved=a.get("resolved", False),
            resolved_at=resolved_at,
            created_at=created_at,
            device=device_info
        ))
    
    return AlertListResponse(
        page=page,
        total=total,
        alerts=alerts
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert_by_id(alert_id: str, user: dict = Depends(get_current_user)):
    """Single alert for mobile/web detail views; scoped to user's (and family) devices."""
    db = await get_database()
    user_id = user["_id"]
    if not isinstance(user_id, ObjectId):
        user_id = ObjectId(user_id)
    try:
        oid = ObjectId(alert_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid alert ID")
    doc = await db.alerts.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    raw_dev = doc.get("deviceId") or doc.get("device_id")
    if not raw_dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    try:
        dev_oid = raw_dev if isinstance(raw_dev, ObjectId) else ObjectId(str(raw_dev))
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    allowed = await _device_ids_for_user_alerts(db, user_id)
    if dev_oid not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this alert")
    return await _alert_document_to_response(db, doc)


@router.delete("/cleanup")
async def cleanup_old_alerts(days: int = Query(..., description="Delete alerts older than this many days")):
    """
    Delete old alerts for housekeeping
    
    WARNING: This permanently deletes alerts!
    """
    db = await get_database()
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    result = await db.alerts.delete_many({"createdAt": {"$lt": cutoff}})
    
    return {
        "message": f"Deleted {result.deleted_count} alerts older than {days} days",
        "deleted_count": result.deleted_count
    }

@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user: dict = Depends(get_current_user)):
    """
    Mark an alert as resolved (only if it belongs to the user's or family's devices).
    """
    db = await get_database()
    user_id = user["_id"]
    if not isinstance(user_id, ObjectId):
        user_id = ObjectId(user_id)
    try:
        oid = ObjectId(alert_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid alert ID")

    allowed = await _device_ids_for_user_alerts(db, user_id)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    result = await db.alerts.update_one(
        {
            "_id": oid,
            "$or": [
                {"deviceId": {"$in": allowed}},
                {"device_id": {"$in": allowed}},
            ],
        },
        {
            "$set": {
                "resolved": True,
                "resolvedAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow(),
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return {"message": "Alert resolved successfully"}


class AlertResolveMultipleRequest(BaseModel):
    alert_ids: List[str] = Field(..., min_items=1, description="List of alert IDs to resolve")


def _get_object_id_list(ids: List[str]) -> List[ObjectId]:
    out: List[ObjectId] = []
    for _id in ids:
        try:
            out.append(ObjectId(_id))
        except Exception:
            continue
    return out


@router.post("/resolve-multiple")
async def resolve_multiple_alerts(
    body: AlertResolveMultipleRequest,
    user: dict = Depends(get_current_user),
):
    """
    Resolve multiple active alerts in one request.

    Ownership check: only resolve alerts that belong to devices owned by the current user.
    """
    db = await get_database()

    user_id = user["_id"]
    if not isinstance(user_id, ObjectId):
        user_id = ObjectId(user_id)

    user_device_ids = await _device_ids_for_user_alerts(db, user_id)
    if not user_device_ids:
        return {"message": "No devices found for this account", "resolved_count": 0}

    alert_obj_ids = _get_object_id_list(body.alert_ids)
    if not alert_obj_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid alert ids provided")

    result = await db.alerts.update_many(
        {
            "_id": {"$in": alert_obj_ids},
            "$or": [
                {"deviceId": {"$in": user_device_ids}},
                {"device_id": {"$in": user_device_ids}},
            ],
            "resolved": {"$ne": True},
        },
        {
            "$set": {
                "resolved": True,
                "resolvedAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow(),
            }
        },
    )

    return {"message": "Alerts resolved successfully", "resolved_count": result.modified_count}


@router.post("/resolve-all")
async def resolve_all_alerts(
    user: dict = Depends(get_current_user),
):
    """
    Resolve all active (unresolved) alerts for devices owned by the current user.
    """
    db = await get_database()

    user_id = user["_id"]
    if not isinstance(user_id, ObjectId):
        user_id = ObjectId(user_id)

    user_device_ids = await _device_ids_for_user_alerts(db, user_id)
    if not user_device_ids:
        return {"message": "No devices found for this account", "resolved_count": 0}

    result = await db.alerts.update_many(
        {
            "$or": [
                {"deviceId": {"$in": user_device_ids}},
                {"device_id": {"$in": user_device_ids}},
            ],
            "resolved": {"$ne": True},
        },
        {
            "$set": {
                "resolved": True,
                "resolvedAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow(),
            }
        },
    )

    return {"message": "All active alerts resolved successfully", "resolved_count": result.modified_count}