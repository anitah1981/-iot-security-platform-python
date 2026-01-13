# routes/exports.py - Alert Export Routes
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timedelta
from bson import ObjectId

from database import get_database
from routes.auth import get_current_user
from services.export_service import ExportService

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
    plan = current_user.get("plan", "free")
    if plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PDF exports are a Pro+ feature. Please upgrade your plan."
        )
    
    # Build filter query
    filter_query = {"user_id": user_id}
    
    # Check if user is in a family
    membership = await db.family_members.find_one({"user_id": user_id})
    if membership:
        filter_query = {"family_id": membership["family_id"]}
    
    # Apply filters
    if severity:
        filter_query["severity"] = severity
    if type:
        filter_query["type"] = type
    
    # Date filter
    since_date = datetime.utcnow() - timedelta(days=days)
    filter_query["created_at"] = {"$gte": since_date}
    
    # Get alerts
    alerts = await db.alerts.find(filter_query).sort("created_at", -1).to_list(1000)
    
    # Get device names for alerts
    for alert in alerts:
        device_id = alert.get("device_id")
        if device_id:
            try:
                device = await db.devices.find_one({"_id": ObjectId(device_id)})
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
    plan = current_user.get("plan", "free")
    if plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSV exports are a Pro+ feature. Please upgrade your plan."
        )
    
    # Build filter query
    filter_query = {"user_id": user_id}
    
    # Check if user is in a family
    membership = await db.family_members.find_one({"user_id": user_id})
    if membership:
        filter_query = {"family_id": membership["family_id"]}
    
    # Apply filters
    if severity:
        filter_query["severity"] = severity
    if type:
        filter_query["type"] = type
    
    # Date filter
    since_date = datetime.utcnow() - timedelta(days=days)
    filter_query["created_at"] = {"$gte": since_date}
    
    # Get alerts
    alerts = await db.alerts.find(filter_query).sort("created_at", -1).to_list(10000)
    
    # Get device names for alerts
    for alert in alerts:
        device_id = alert.get("device_id")
        if device_id:
            try:
                device = await db.devices.find_one({"_id": ObjectId(device_id)})
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
