# routes/incidents.py - Incident Management Routes
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from database import get_database
from routes.auth import get_current_user
from models import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentListResponse,
    IncidentNoteCreate,
    IncidentNote,
    TimelineEvent
)
from services.incident_correlator import IncidentCorrelator
from middleware.plan_limits import PlanLimits

router = APIRouter()


@router.get("/", response_model=IncidentListResponse)
async def get_incidents(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get incidents for current user (Pro/Business plan feature)
    """
    # Check plan
    await PlanLimits.check_feature_access(current_user, "incident_timeline")
    
    db = await get_database()
    user_id = current_user["_id"]
    
    # Build filter
    filter_query = {"user_id": user_id}
    if status:
        filter_query["status"] = status
    if severity:
        filter_query["severity"] = severity
    
    # Get total count
    total = await db.incidents.count_documents(filter_query)
    
    # Calculate pagination
    skip = (page - 1) * limit
    
    # Get incidents
    incidents_raw = await db.incidents.find(filter_query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Shape response
    incidents = []
    for inc in incidents_raw:
        # Get notes
        notes_raw = await db.incident_notes.find({"incident_id": inc["_id"]}).sort("created_at", 1).to_list(100)
        notes = [
            IncidentNote(
                id=str(n["_id"]),
                incident_id=str(n["incident_id"]),
                user_id=str(n["user_id"]),
                user_name=n.get("user_name", ""),
                content=n.get("content", ""),
                created_at=n["created_at"]
            )
            for n in notes_raw
        ]
        
        # Calculate time to resolution
        time_to_resolution = None
        if inc.get("resolved_at") and inc.get("created_at"):
            delta = inc["resolved_at"] - inc["created_at"]
            time_to_resolution = int(delta.total_seconds() / 60)
        
        incidents.append(IncidentResponse(
            id=str(inc["_id"]),
            user_id=str(inc["user_id"]),
            title=inc["title"],
            description=inc.get("description"),
            severity=inc.get("severity", "medium"),
            status=inc.get("status", "open"),
            alert_ids=[str(aid) for aid in inc.get("alert_ids", [])],
            notes=notes,
            created_at=inc["created_at"],
            updated_at=inc.get("updated_at", inc["created_at"]),
            resolved_at=inc.get("resolved_at"),
            time_to_resolution_minutes=time_to_resolution
        ))
    
    return IncidentListResponse(
        page=page,
        total=total,
        incidents=incidents
    )


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident: IncidentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new incident (Pro/Business plan feature)
    """
    # Check plan
    await PlanLimits.check_feature_access(current_user, "incident_timeline")
    
    db = await get_database()
    user_id = current_user["_id"]
    
    # Validate alert IDs if provided
    alert_ids = []
    if incident.alert_ids:
        for alert_id_str in incident.alert_ids:
            try:
                alert_obj_id = ObjectId(alert_id_str)
                # Verify alert exists and belongs to user
                alert = await db.alerts.find_one({"_id": alert_obj_id})
                if alert:
                    # Check if alert is from user's device
                    device_id = alert.get("deviceId") or alert.get("device_id")
                    if device_id:
                        device = await db.devices.find_one({"_id": ObjectId(device_id), "user_id": user_id})
                        if device:
                            alert_ids.append(alert_obj_id)
            except:
                pass  # Skip invalid alert IDs
    
    # Create incident
    incident_doc = {
        "user_id": user_id,
        "title": incident.title,
        "description": incident.description,
        "severity": incident.severity,
        "status": incident.status,
        "alert_ids": alert_ids,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.incidents.insert_one(incident_doc)
    incident_doc["_id"] = result.inserted_id
    
    return IncidentResponse(
        id=str(incident_doc["_id"]),
        user_id=str(user_id),
        title=incident_doc["title"],
        description=incident_doc.get("description"),
        severity=incident_doc["severity"],
        status=incident_doc["status"],
        alert_ids=[str(aid) for aid in alert_ids],
        notes=[],
        created_at=incident_doc["created_at"],
        updated_at=incident_doc["updated_at"],
        resolved_at=None,
        time_to_resolution_minutes=None
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get incident details (Pro/Business plan feature)
    """
    # Check plan
    await PlanLimits.check_feature_access(current_user, "incident_timeline")
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        incident_obj_id = ObjectId(incident_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid incident ID"
        )
    
    # Get incident
    inc = await db.incidents.find_one({"_id": incident_obj_id, "user_id": user_id})
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Get notes
    notes_raw = await db.incident_notes.find({"incident_id": incident_obj_id}).sort("created_at", 1).to_list(100)
    notes = [
        IncidentNote(
            id=str(n["_id"]),
            incident_id=str(n["incident_id"]),
            user_id=str(n["user_id"]),
            user_name=n.get("user_name", ""),
            content=n.get("content", ""),
            created_at=n["created_at"]
        )
        for n in notes_raw
    ]
    
    # Calculate time to resolution
    time_to_resolution = None
    if inc.get("resolved_at") and inc.get("created_at"):
        delta = inc["resolved_at"] - inc["created_at"]
        time_to_resolution = int(delta.total_seconds() / 60)
    
    return IncidentResponse(
        id=str(inc["_id"]),
        user_id=str(inc["user_id"]),
        title=inc["title"],
        description=inc.get("description"),
        severity=inc.get("severity", "medium"),
        status=inc.get("status", "open"),
        alert_ids=[str(aid) for aid in inc.get("alert_ids", [])],
        notes=notes,
        created_at=inc["created_at"],
        updated_at=inc.get("updated_at", inc["created_at"]),
        resolved_at=inc.get("resolved_at"),
        time_to_resolution_minutes=time_to_resolution
    )


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    incident_update: IncidentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update incident (Pro/Business plan feature)
    """
    # Check plan
    await PlanLimits.check_feature_access(current_user, "incident_timeline")
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        incident_obj_id = ObjectId(incident_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid incident ID"
        )
    
    # Check ownership
    inc = await db.incidents.find_one({"_id": incident_obj_id, "user_id": user_id})
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Build update
    update_data = {}
    for field, value in incident_update.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    # Handle status change to resolved
    if update_data.get("status") == "resolved" and inc.get("status") != "resolved":
        update_data["resolved_at"] = datetime.utcnow()
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db.incidents.update_one(
            {"_id": incident_obj_id},
            {"$set": update_data}
        )
    
    # Get updated incident
    updated_inc = await db.incidents.find_one({"_id": incident_obj_id})
    
    # Get notes
    notes_raw = await db.incident_notes.find({"incident_id": incident_obj_id}).sort("created_at", 1).to_list(100)
    notes = [
        IncidentNote(
            id=str(n["_id"]),
            incident_id=str(n["incident_id"]),
            user_id=str(n["user_id"]),
            user_name=n.get("user_name", ""),
            content=n.get("content", ""),
            created_at=n["created_at"]
        )
        for n in notes_raw
    ]
    
    # Calculate time to resolution
    time_to_resolution = None
    if updated_inc.get("resolved_at") and updated_inc.get("created_at"):
        delta = updated_inc["resolved_at"] - updated_inc["created_at"]
        time_to_resolution = int(delta.total_seconds() / 60)
    
    return IncidentResponse(
        id=str(updated_inc["_id"]),
        user_id=str(updated_inc["user_id"]),
        title=updated_inc["title"],
        description=updated_inc.get("description"),
        severity=updated_inc.get("severity", "medium"),
        status=updated_inc.get("status", "open"),
        alert_ids=[str(aid) for aid in updated_inc.get("alert_ids", [])],
        notes=notes,
        created_at=updated_inc["created_at"],
        updated_at=updated_inc.get("updated_at", updated_inc["created_at"]),
        resolved_at=updated_inc.get("resolved_at"),
        time_to_resolution_minutes=time_to_resolution
    )


@router.post("/{incident_id}/notes", response_model=IncidentNote, status_code=status.HTTP_201_CREATED)
async def add_incident_note(
    incident_id: str,
    note: IncidentNoteCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a note to an incident (Pro/Business plan feature)
    """
    # Check plan
    await PlanLimits.check_feature_access(current_user, "incident_timeline")
    
    db = await get_database()
    user_id = current_user["_id"]
    user_name = current_user.get("name", "Unknown User")
    
    try:
        incident_obj_id = ObjectId(incident_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid incident ID"
        )
    
    # Check ownership
    inc = await db.incidents.find_one({"_id": incident_obj_id, "user_id": user_id})
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Create note
    note_doc = {
        "incident_id": incident_obj_id,
        "user_id": user_id,
        "user_name": user_name,
        "content": note.content,
        "created_at": datetime.utcnow()
    }
    
    result = await db.incident_notes.insert_one(note_doc)
    note_doc["_id"] = result.inserted_id
    
    return IncidentNote(
        id=str(note_doc["_id"]),
        incident_id=str(incident_obj_id),
        user_id=str(user_id),
        user_name=user_name,
        content=note_doc["content"],
        created_at=note_doc["created_at"]
    )


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark incident as resolved (Pro/Business plan feature)
    """
    # Check plan
    await PlanLimits.check_feature_access(current_user, "incident_timeline")
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        incident_obj_id = ObjectId(incident_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid incident ID"
        )
    
    # Check ownership
    inc = await db.incidents.find_one({"_id": incident_obj_id, "user_id": user_id})
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Update to resolved
    resolved_at = datetime.utcnow()
    await db.incidents.update_one(
        {"_id": incident_obj_id},
        {"$set": {
            "status": "resolved",
            "resolved_at": resolved_at,
            "updated_at": resolved_at
        }}
    )
    
    # Get updated incident
    updated_inc = await db.incidents.find_one({"_id": incident_obj_id})
    
    # Get notes
    notes_raw = await db.incident_notes.find({"incident_id": incident_obj_id}).sort("created_at", 1).to_list(100)
    notes = [
        IncidentNote(
            id=str(n["_id"]),
            incident_id=str(n["incident_id"]),
            user_id=str(n["user_id"]),
            user_name=n.get("user_name", ""),
            content=n.get("content", ""),
            created_at=n["created_at"]
        )
        for n in notes_raw
    ]
    
    # Calculate time to resolution
    time_to_resolution = None
    if updated_inc.get("resolved_at") and updated_inc.get("created_at"):
        delta = updated_inc["resolved_at"] - updated_inc["created_at"]
        time_to_resolution = int(delta.total_seconds() / 60)
    
    return IncidentResponse(
        id=str(updated_inc["_id"]),
        user_id=str(updated_inc["user_id"]),
        title=updated_inc["title"],
        description=updated_inc.get("description"),
        severity=updated_inc.get("severity", "medium"),
        status="resolved",
        alert_ids=[str(aid) for aid in updated_inc.get("alert_ids", [])],
        notes=notes,
        created_at=updated_inc["created_at"],
        updated_at=updated_inc.get("updated_at", updated_inc["created_at"]),
        resolved_at=resolved_at,
        time_to_resolution_minutes=time_to_resolution
    )


@router.get("/{incident_id}/timeline", response_model=List[TimelineEvent])
async def get_incident_timeline(
    incident_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get timeline of events for an incident (Pro/Business plan feature)
    """
    # Check plan
    await PlanLimits.check_feature_access(current_user, "incident_timeline")
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        incident_obj_id = ObjectId(incident_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid incident ID"
        )
    
    # Check ownership
    inc = await db.incidents.find_one({"_id": incident_obj_id, "user_id": user_id})
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    timeline_events = []
    
    # Add incident creation event
    timeline_events.append(TimelineEvent(
        id=f"incident_{incident_obj_id}",
        type="incident_created",
        timestamp=inc["created_at"],
        title="Incident Created",
        description=inc.get("description"),
        severity=inc.get("severity", "medium"),
        user_name=current_user.get("name", "Unknown"),
        metadata={"status": inc.get("status", "open")}
    ))
    
    # Add alert events
    for alert_id in inc.get("alert_ids", []):
        try:
            alert = await db.alerts.find_one({"_id": ObjectId(alert_id)})
            if alert:
                created_at = alert.get("createdAt") or alert.get("created_at")
                timeline_events.append(TimelineEvent(
                    id=f"alert_{alert_id}",
                    type="alert",
                    timestamp=created_at if created_at else inc["created_at"],
                    title=alert.get("message", "Alert"),
                    description=f"Severity: {alert.get('severity', 'medium')}",
                    severity=alert.get("severity", "medium"),
                    metadata={
                        "alert_id": str(alert_id),
                        "alert_type": alert.get("type", "system")
                    }
                ))
        except:
            pass
    
    # Add note events
    notes = await db.incident_notes.find({"incident_id": incident_obj_id}).sort("created_at", 1).to_list(100)
    for note in notes:
        timeline_events.append(TimelineEvent(
            id=f"note_{note['_id']}",
            type="note",
            timestamp=note["created_at"],
            title="Note Added",
            description=note.get("content", ""),
            user_name=note.get("user_name", "Unknown"),
            metadata={}
        ))
    
    # Add status change events
    if inc.get("resolved_at"):
        timeline_events.append(TimelineEvent(
            id=f"resolved_{incident_obj_id}",
            type="status_change",
            timestamp=inc["resolved_at"],
            title="Incident Resolved",
            description="Incident marked as resolved",
            user_name=current_user.get("name", "Unknown"),
            metadata={"status": "resolved"}
        ))
    
    # Sort by timestamp
    timeline_events.sort(key=lambda e: e.timestamp)
    
    return timeline_events


@router.get("/suggestions/correlate", response_model=List[dict])
async def get_correlation_suggestions(
    time_window_minutes: int = Query(30, ge=1, le=1440),
    current_user: dict = Depends(get_current_user)
):
    """
    Get suggested incident correlations from unresolved alerts (Pro/Business plan feature)
    """
    # Check plan
    await PlanLimits.check_feature_access(current_user, "incident_timeline")
    
    db = await get_database()
    user_id = current_user["_id"]
    
    # Get correlation suggestions
    suggestions = await IncidentCorrelator.correlate_alerts(
        db=db,
        user_id=user_id,
        time_window_minutes=time_window_minutes,
        device_grouping=True
    )
    
    return suggestions
