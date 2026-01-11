# routes/alerts.py - Alert Management Routes
from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks
from typing import Optional
from bson import ObjectId
from datetime import datetime, timedelta

from models import AlertCreate, AlertResponse, AlertListResponse
from database import get_database

router = APIRouter()

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

@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
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
    if not allow_duplicate:
        query = {
            "deviceId": ObjectId(alert.device_id),
            "message": alert.message,
            "type": alert.type,
            "severity": alert.severity
        }
        
        if time_window:
            cutoff = datetime.utcnow() - timedelta(seconds=time_window)
            query["createdAt"] = {"$gte": cutoff}
        
        existing_alert = await db.alerts.find_one(query)
        
        if existing_alert:
            return AlertResponse(
                id=str(existing_alert["_id"]),
                device_id=str(existing_alert["deviceId"]),
                message=existing_alert["message"],
                severity=existing_alert["severity"],
                type=existing_alert["type"],
                context=existing_alert.get("context", {}),
                resolved=existing_alert.get("resolved", False),
                resolved_at=existing_alert.get("resolvedAt"),
                created_at=existing_alert["createdAt"]
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

@router.get("/", response_model=AlertListResponse)
async def get_alerts(
    device_id: Optional[str] = Query(None, description="Filter by device MongoDB ObjectId"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    type: Optional[str] = Query(None, description="Filter by alert type"),
    since: Optional[datetime] = Query(None, description="Only alerts after this timestamp"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Get alerts with filters and pagination
    
    Query params:
    - device_id: Filter by device (MongoDB ObjectId)
    - severity: Filter by severity (critical, high, medium, low)
    - type: Filter by type (connectivity, power, security, system)
    - since: Only alerts after this timestamp
    - page: Page number
    - limit: Items per page
    """
    db = await get_database()
    
    # Build filter
    filter_query = {}
    if device_id:
        filter_query["deviceId"] = ObjectId(device_id)
    if severity:
        filter_query["severity"] = severity
    if type:
        filter_query["type"] = type
    if since:
        filter_query["createdAt"] = {"$gte": since}
    
    # Calculate skip
    skip = (page - 1) * limit
    
    # Get alerts
    cursor = db.alerts.find(filter_query).sort("createdAt", -1).skip(skip).limit(limit)
    alerts_raw = await cursor.to_list(length=limit)
    
    # Get total count
    total = await db.alerts.count_documents(filter_query)
    
    # Shape response with device info
    alerts = []
    for a in alerts_raw:
        # Get device info
        device_info = None
        if a.get("deviceId"):
            device = await db.devices.find_one({"_id": a["deviceId"]})
            if device:
                device_info = {
                    "id": str(device["_id"]),
                    "logical_id": device.get("deviceId"),
                    "name": device.get("name"),
                    "type": device.get("type")
                }
        
        alerts.append(AlertResponse(
            id=str(a["_id"]),
            device_id=str(a["deviceId"]),
            message=a["message"],
            severity=a["severity"],
            type=a["type"],
            context=a.get("context", {}),
            resolved=a.get("resolved", False),
            resolved_at=a.get("resolvedAt"),
            created_at=a["createdAt"],
            device=device_info
        ))
    
    return AlertListResponse(
        page=page,
        total=total,
        alerts=alerts
    )

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

@router.patch("/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """
    Mark an alert as resolved
    """
    db = await get_database()
    
    result = await db.alerts.update_one(
        {"_id": ObjectId(alert_id)},
        {
            "$set": {
                "resolved": True,
                "resolvedAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {"message": "Alert resolved successfully"}