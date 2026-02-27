# routes/audit.py - Audit Log Routes
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
import csv
import io

from database import get_database
from routes.auth import require_business_plan
from models import AuditLogEntry

router = APIRouter()


@router.get("/logs")
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    current_user: dict = Depends(require_business_plan),
):
    """
    Get audit logs with pagination (Business plan feature)
    """
    db = await get_database()
    user_id = current_user["_id"]
    
    # Build filter
    filter_query = {"user_id": user_id}
    
    # Check if user is in a family (show all family logs for admin)
    membership = await db.family_members.find_one({"user_id": user_id})
    if membership and membership["role"] == "admin":
        # Show logs for all family members
        family_members = await db.family_members.find(
            {"family_id": membership["family_id"]}
        ).to_list(100)
        member_ids = [m["user_id"] for m in family_members]
        filter_query = {"user_id": {"$in": member_ids}}
    
    # Apply filters
    if action:
        filter_query["action"] = action
    if resource_type:
        filter_query["resource_type"] = resource_type
    
    # Date filter
    since_date = datetime.utcnow() - timedelta(days=days)
    filter_query["created_at"] = {"$gte": since_date}
    
    # Get total count
    total = await db.audit_logs.count_documents(filter_query)
    
    # Calculate pagination
    skip = (page - 1) * limit
    
    # Get logs
    logs = await db.audit_logs.find(filter_query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "logs": [
            AuditLogEntry(
                id=str(log["_id"]),
                user_id=str(log["user_id"]),
                user_email=log["user_email"],
                user_name=log["user_name"],
                action=log["action"],
                resource_type=log["resource_type"],
                resource_id=log.get("resource_id"),
                details=log.get("details", {}),
                ip_address=log.get("ip_address"),
                user_agent=log.get("user_agent"),
                created_at=log["created_at"]
            )
            for log in logs
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 0
    }


@router.get("/logs/stats")
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_business_plan),
):
    """Get audit log statistics (Business plan feature)"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Build filter (same as get_audit_logs)
    filter_query = {"user_id": user_id}
    membership = await db.family_members.find_one({"user_id": user_id})
    if membership and membership["role"] == "admin":
        family_members = await db.family_members.find(
            {"family_id": membership["family_id"]}
        ).to_list(100)
        member_ids = [m["user_id"] for m in family_members]
        filter_query = {"user_id": {"$in": member_ids}}
    
    # Date range
    since_date = datetime.utcnow() - timedelta(days=days)
    filter_query["created_at"] = {"$gte": since_date}
    
    # Get action breakdown
    pipeline = [
        {"$match": filter_query},
        {"$group": {"_id": "$action", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    action_counts = {}
    async for item in db.audit_logs.aggregate(pipeline):
        action_counts[item["_id"]] = item["count"]
    
    # Get resource type breakdown
    resource_pipeline = [
        {"$match": filter_query},
        {"$group": {"_id": "$resource_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    resource_counts = {}
    async for item in db.audit_logs.aggregate(resource_pipeline):
        resource_counts[item["_id"]] = item["count"]
    
    # Total logs
    total_logs = await db.audit_logs.count_documents(filter_query)
    
    return {
        "total_logs": total_logs,
        "action_breakdown": action_counts,
        "resource_breakdown": resource_counts,
        "period_days": days
    }


@router.get("/logs/export")
async def export_audit_logs(
    format: str = Query("csv", description="Export format: csv or json"),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_business_plan),
):
    """Export audit logs (Business plan feature)"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Build filter (same as get_audit_logs)
    filter_query = {"user_id": user_id}
    membership = await db.family_members.find_one({"user_id": user_id})
    if membership and membership["role"] == "admin":
        family_members = await db.family_members.find(
            {"family_id": membership["family_id"]}
        ).to_list(100)
        member_ids = [m["user_id"] for m in family_members]
        filter_query = {"user_id": {"$in": member_ids}}
    
    if action:
        filter_query["action"] = action
    if resource_type:
        filter_query["resource_type"] = resource_type
    
    since_date = datetime.utcnow() - timedelta(days=days)
    filter_query["created_at"] = {"$gte": since_date}
    
    # Get all logs (no pagination for export)
    logs = await db.audit_logs.find(filter_query).sort("created_at", -1).to_list(10000)
    
    if format.lower() == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Timestamp", "User Email", "User Name", "Action", "Resource Type",
            "Resource ID", "IP Address", "User Agent", "Details"
        ])
        
        # Data rows
        for log in logs:
            details_str = str(log.get("details", {}))
            writer.writerow([
                log["created_at"].isoformat() if log.get("created_at") else "",
                log.get("user_email", ""),
                log.get("user_name", ""),
                log.get("action", ""),
                log.get("resource_type", ""),
                log.get("resource_id", ""),
                log.get("ip_address", ""),
                log.get("user_agent", ""),
                details_str
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="audit_logs_{datetime.utcnow().strftime("%Y%m%d")}.csv"'
            }
        )
    else:
        # JSON export
        logs_data = [
            {
                "id": str(log["_id"]),
                "user_id": str(log["user_id"]),
                "user_email": log.get("user_email", ""),
                "user_name": log.get("user_name", ""),
                "action": log.get("action", ""),
                "resource_type": log.get("resource_type", ""),
                "resource_id": log.get("resource_id"),
                "details": log.get("details", {}),
                "ip_address": log.get("ip_address"),
                "user_agent": log.get("user_agent"),
                "created_at": log["created_at"].isoformat() if log.get("created_at") else ""
            }
            for log in logs
        ]
        
        import json
        json_content = json.dumps(logs_data, indent=2, default=str)
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="audit_logs_{datetime.utcnow().strftime("%Y%m%d")}.json"'
            }
        )
