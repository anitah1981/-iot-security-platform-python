# routes/analytics.py - Analytics & Dashboard Statistics
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from typing import Dict, Any, List
from bson import ObjectId

from database import get_database
from routes.auth import get_current_user

router = APIRouter()


@router.get("/devices/stats")
async def get_device_stats(current_user: dict = Depends(get_current_user)):
    """Get device statistics for charts"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Get all user devices (check both user_id and userId for compatibility)
    devices = await db.devices.find({
        "$or": [
            {"user_id": user_id},
            {"userId": user_id}
        ]
    }).to_list(1000)
    
    # Device status breakdown
    status_counts = {"online": 0, "offline": 0, "error": 0}
    type_counts = {}
    
    for device in devices:
        status = device.get("status", "offline")
        status_counts[status] = status_counts.get(status, 0) + 1
        
        device_type = device.get("type", "Unknown")
        type_counts[device_type] = type_counts.get(device_type, 0) + 1
    
    # Device growth over last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    growth_data = []
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        count = await db.devices.count_documents({
            "$or": [
                {"user_id": user_id, "created_at": {"$lte": date}},
                {"userId": user_id, "createdAt": {"$lte": date}},
                {"user_id": user_id, "createdAt": {"$lte": date}},
                {"userId": user_id, "created_at": {"$lte": date}}
            ]
        })
        growth_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "count": count
        })
    
    return {
        "total_devices": len(devices),
        "status_breakdown": status_counts,
        "type_breakdown": type_counts,
        "growth_timeline": growth_data
    }


@router.get("/alerts/trends")
async def get_alert_trends(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get alert trends for charts"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Get date range
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all alerts in range (check both user_id and userId for compatibility)
    alerts = await db.alerts.find({
        "$or": [
            {"user_id": user_id},
            {"userId": user_id}
        ],
        "created_at": {"$gte": start_date}
    }).to_list(10000)
    
    # Alerts by severity
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    
    # Alerts by type
    type_counts = {}
    
    # Alerts per day
    daily_counts = {}
    
    # Alerts by severity per day (for stacked chart)
    daily_severity = {}
    
    for alert in alerts:
        # Severity breakdown
        severity = alert.get("severity", "low")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Type breakdown
        alert_type = alert.get("type", "system")
        type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
        
        # Daily counts
        date_str = alert["created_at"].strftime("%Y-%m-%d")
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
        
        # Daily severity breakdown
        if date_str not in daily_severity:
            daily_severity[date_str] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        daily_severity[date_str][severity] += 1
    
    # Fill in missing days with 0
    timeline = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        timeline.append({
            "date": date_str,
            "count": daily_counts.get(date_str, 0),
            "by_severity": daily_severity.get(date_str, {"low": 0, "medium": 0, "high": 0, "critical": 0})
        })
    
    # Resolution stats
    total_alerts = len(alerts)
    resolved_alerts = len([a for a in alerts if a.get("resolved", False)])
    resolution_rate = (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0
    
    # Average resolution time (for resolved alerts)
    resolution_times = []
    for alert in alerts:
        if alert.get("resolved") and alert.get("resolved_at"):
            time_diff = (alert["resolved_at"] - alert["created_at"]).total_seconds() / 60  # minutes
            resolution_times.append(time_diff)
    
    avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    return {
        "total_alerts": total_alerts,
        "severity_breakdown": severity_counts,
        "type_breakdown": type_counts,
        "timeline": timeline,
        "resolution_rate": round(resolution_rate, 1),
        "avg_resolution_time_minutes": round(avg_resolution_time, 1),
        "resolved_count": resolved_alerts,
        "unresolved_count": total_alerts - resolved_alerts
    }


@router.get("/health/metrics")
async def get_health_metrics(current_user: dict = Depends(get_current_user)):
    """Get system health metrics"""
    db = await get_database()
    user_id = current_user["_id"]
    
    # Get all devices (check both user_id and userId for compatibility)
    devices = await db.devices.find({
        "$or": [
            {"user_id": user_id},
            {"userId": user_id}
        ]
    }).to_list(1000)
    
    # Calculate uptime percentage
    online_devices = len([d for d in devices if d.get("status") == "online"])
    uptime_percentage = (online_devices / len(devices) * 100) if devices else 0
    
    # Get alerts from last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_alerts = await db.alerts.count_documents({
        "$or": [
            {"user_id": user_id},
            {"userId": user_id}
        ],
        "created_at": {"$gte": yesterday}
    })
    
    # Top 5 devices with most alerts (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    pipeline = [
        {"$match": {
            "$or": [
                {"user_id": user_id},
                {"userId": user_id}
            ],
            "created_at": {"$gte": thirty_days_ago}
        }},
        {"$group": {"_id": "$device_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    
    top_alerting_devices = []
    async for item in db.alerts.aggregate(pipeline):
        device_id = item["_id"]
        # Get device details
        try:
            device = await db.devices.find_one({"_id": ObjectId(device_id)})
            if device:
                top_alerting_devices.append({
                    "device_name": device.get("name", "Unknown"),
                    "device_type": device.get("type", "Unknown"),
                    "alert_count": item["count"]
                })
        except:
            pass
    
    # System health score (0-100)
    # Based on: uptime (50%), alert frequency (30%), resolution rate (20%)
    alerts_last_week = await db.alerts.count_documents({
        "$or": [
            {"user_id": user_id},
            {"userId": user_id}
        ],
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
    })
    
    # Lower score if many alerts per device
    alert_frequency_score = max(0, 100 - (alerts_last_week / max(len(devices), 1) * 10))
    
    resolved_last_week = await db.alerts.count_documents({
        "$or": [
            {"user_id": user_id},
            {"userId": user_id}
        ],
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)},
        "resolved": True
    })
    
    resolution_score = (resolved_last_week / alerts_last_week * 100) if alerts_last_week > 0 else 100
    
    health_score = (
        uptime_percentage * 0.5 +
        alert_frequency_score * 0.3 +
        resolution_score * 0.2
    )
    
    return {
        "uptime_percentage": round(uptime_percentage, 1),
        "total_devices": len(devices),
        "online_devices": online_devices,
        "offline_devices": len(devices) - online_devices,
        "alerts_last_24h": recent_alerts,
        "top_alerting_devices": top_alerting_devices,
        "health_score": round(health_score, 1)
    }
