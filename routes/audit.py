# routes/audit.py - Audit Log Routes
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId

from database import get_database
from routes.auth import get_current_user
from models import AuditLogEntry

router = APIRouter()


@router.get("/logs", response_model=List[AuditLogEntry])
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit logs (Business plan feature)
    """
    db = await get_database()
    user_id = current_user["_id"]
    
    # Check plan (Business only)
    plan = current_user.get("plan", "free")
    if plan != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Audit logs are a Business plan feature. Please upgrade your plan."
        )
    
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
    
    # Get logs
    logs = await db.audit_logs.find(filter_query).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [
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
    ]


@router.get("/logs/stats")
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get audit log statistics"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Check plan
    plan = current_user.get("plan", "free")
    if plan != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Audit logs are a Business plan feature."
        )
    
    # Date range
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get action breakdown
    pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": since_date}}},
        {"$group": {"_id": "$action", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    action_counts = {}
    async for item in db.audit_logs.aggregate(pipeline):
        action_counts[item["_id"]] = item["count"]
    
    # Total logs
    total_logs = await db.audit_logs.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": since_date}
    })
    
    return {
        "total_logs": total_logs,
        "action_breakdown": action_counts,
        "period_days": days
    }
