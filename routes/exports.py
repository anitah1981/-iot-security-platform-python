# routes/exports.py - Alert Export Routes
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timedelta
from bson import ObjectId

from database import get_database
from routes.auth import get_current_user
from services.export_service import ExportService
from middleware.plan_limits import get_effective_plan

router = APIRouter()


@router.post("/pdf")
async def export_alerts_pdf(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    type: Optional[str] = Query(None, description="Filter by type"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export alerts as PDF report with charts and statistics
    Pro+ feature
    """
    db = await get_database()
    user_id = current_user["_id"]
    
    # Check plan (Pro or Business)
    plan = get_effective_plan(current_user)
    if plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PDF exports are a Pro+ feature. Please upgrade your plan."
        )
    
    # Build filter: same as GET /alerts – alerts are linked by device (deviceId/device_id), not user_id
    uid = user_id if isinstance(user_id, ObjectId) else ObjectId(user_id)
    user_devices = await db.devices.find({
        "$or": [{"userId": uid}, {"user_id": uid}],
        "isDeleted": {"$ne": True}
    }).to_list(length=1000)
    user_device_ids = [ObjectId(d["_id"]) for d in user_devices]
    since_date = datetime.utcnow() - timedelta(days=days)
    filter_parts = [
        {"$or": [{"deviceId": {"$in": user_device_ids}}, {"device_id": {"$in": user_device_ids}}]},
        {"$or": [{"createdAt": {"$gte": since_date}}, {"created_at": {"$gte": since_date}}]}
    ]
    if severity:
        filter_parts.append({"severity": severity})
    if type:
        filter_parts.append({"type": type})
    filter_query = {"$and": filter_parts} if user_device_ids else {"_id": None}
    alerts_raw = await db.alerts.find(filter_query).sort([("createdAt", -1), ("created_at", -1)]).to_list(1000)
    # Normalize for export service (expects created_at, resolved_at, device_id)
    alerts = []
    for a in alerts_raw:
        a["created_at"] = a.get("created_at") or a.get("createdAt") or datetime.utcnow()
        a["resolved_at"] = a.get("resolved_at") or a.get("resolvedAt")
        a["device_id"] = a.get("device_id") or str(a.get("deviceId", ""))
        alerts.append(a)
    for alert in alerts:
        device_id = alert.get("device_id") or alert.get("deviceId")
        if device_id:
            try:
                did = ObjectId(device_id) if not isinstance(device_id, ObjectId) else device_id
                device = await db.devices.find_one({"_id": did})
                if device:
                    alert["device"] = {
                        "name": device.get("name", "Unknown"),
                        "type": device.get("type", "Unknown")
                    }
            except:
                pass
    
    # Generate PDF
    filters = {"severity": severity, "type": type, "since": since_date}
    pdf_buffer = ExportService.generate_pdf_report(
        alerts=alerts,
        user_name=current_user["name"],
        filters=filters
    )
    
    # Save export history
    filename = f"alerts_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_size = len(pdf_buffer.getvalue())
    
    await ExportService.save_export_history(
        db=db,
        user_id=user_id,
        export_type="pdf",
        filename=filename,
        file_size=file_size,
        alert_count=len(alerts)
    )
    
    # Return PDF
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/csv")
async def export_alerts_csv(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    type: Optional[str] = Query(None, description="Filter by type"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export alerts as CSV file
    Pro+ feature
    """
    db = await get_database()
    user_id = current_user["_id"]
    
    # Check plan (Pro or Business)
    plan = get_effective_plan(current_user)
    if plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSV exports are a Pro+ feature. Please upgrade your plan."
        )
    
    # Build filter: same as GET /alerts – by user's devices and date (createdAt or created_at)
    uid = user_id if isinstance(user_id, ObjectId) else ObjectId(user_id)
    user_devices = await db.devices.find({
        "$or": [{"userId": uid}, {"user_id": uid}],
        "isDeleted": {"$ne": True}
    }).to_list(length=1000)
    user_device_ids = [ObjectId(d["_id"]) for d in user_devices]
    since_date = datetime.utcnow() - timedelta(days=days)
    filter_parts = [
        {"$or": [{"deviceId": {"$in": user_device_ids}}, {"device_id": {"$in": user_device_ids}}]},
        {"$or": [{"createdAt": {"$gte": since_date}}, {"created_at": {"$gte": since_date}}]}
    ]
    if severity:
        filter_parts.append({"severity": severity})
    if type:
        filter_parts.append({"type": type})
    filter_query = {"$and": filter_parts} if user_device_ids else {"_id": None}
    alerts_raw = await db.alerts.find(filter_query).sort([("createdAt", -1), ("created_at", -1)]).to_list(10000)
    alerts = []
    for a in alerts_raw:
        a["created_at"] = a.get("created_at") or a.get("createdAt") or datetime.utcnow()
        a["resolved_at"] = a.get("resolved_at") or a.get("resolvedAt")
        a["device_id"] = a.get("device_id") or str(a.get("deviceId", ""))
        alerts.append(a)
    for alert in alerts:
        device_id = alert.get("device_id") or alert.get("deviceId")
        if device_id:
            try:
                did = ObjectId(device_id) if not isinstance(device_id, ObjectId) else device_id
                device = await db.devices.find_one({"_id": did})
                if device:
                    alert["device"] = {
                        "name": device.get("name", "Unknown"),
                        "type": device.get("type", "Unknown")
                    }
            except:
                pass
    
    # Generate CSV
    csv_buffer = ExportService.generate_csv_export(alerts)
    
    # Save export history
    filename = f"alerts_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    file_size = len(csv_buffer.getvalue())
    
    await ExportService.save_export_history(
        db=db,
        user_id=user_id,
        export_type="csv",
        filename=filename,
        file_size=file_size,
        alert_count=len(alerts)
    )
    
    # Return CSV
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/history")
async def get_export_history(
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get export history for current user"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Get recent exports
    exports = await db.exports.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "exports": [
            {
                "id": str(export["_id"]),
                "type": export["export_type"],
                "filename": export["filename"],
                "file_size": export["file_size"],
                "alert_count": export["alert_count"],
                "created_at": export["created_at"]
            }
            for export in exports
        ]
    }
