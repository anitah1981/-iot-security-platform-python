# services/incident_correlator.py - Incident Correlation Service
from datetime import datetime, timedelta
from typing import List, Dict, Any
from bson import ObjectId


class IncidentCorrelator:
    """Service for correlating alerts into incidents"""
    
    @staticmethod
    def calculate_incident_severity(alert_severities: List[str]) -> str:
        """
        Calculate incident severity based on associated alerts
        Highest severity wins
        """
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        max_severity = "low"
        max_value = 0
        
        for severity in alert_severities:
            value = severity_order.get(severity.lower(), 0)
            if value > max_value:
                max_value = value
                max_severity = severity.lower()
        
        return max_severity
    
    @staticmethod
    async def correlate_alerts(
        db,
        user_id: ObjectId,
        time_window_minutes: int = 30,
        device_grouping: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Correlate unresolved alerts into potential incidents
        
        Args:
            db: Database connection
            user_id: User ID to filter alerts
            time_window_minutes: Time window for correlation (default 30 minutes)
            device_grouping: Group alerts by device (default True)
        
        Returns:
            List of correlated alert groups (potential incidents)
        """
        # Get unresolved alerts for user
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        # Get user's devices
        user_devices = await db.devices.find({"user_id": user_id}).to_list(100)
        device_ids = [d["_id"] for d in user_devices]
        
        if not device_ids:
            return []
        
        # Get unresolved alerts (support both deviceId/device_id and createdAt/created_at)
        alerts = await db.alerts.find({
            "$and": [
                {
                    "$or": [
                        {"deviceId": {"$in": device_ids}},
                        {"device_id": {"$in": device_ids}}
                    ]
                },
                {
                    "$or": [
                        {"createdAt": {"$gte": cutoff_time}},
                        {"created_at": {"$gte": cutoff_time}}
                    ]
                }
            ],
            "resolved": False,
        }).sort("createdAt", -1).to_list(100)
        
        if not alerts:
            return []
        
        # Group alerts by correlation rules
        correlated_groups = []
        
        if device_grouping:
            # Group by device
            device_groups: Dict[str, List[Dict]] = {}
            for alert in alerts:
                device_id = str(alert.get("deviceId") or alert.get("device_id", ""))
                if device_id not in device_groups:
                    device_groups[device_id] = []
                device_groups[device_id].append(alert)
            
            # Create incident suggestions for each device group
            for device_id, device_alerts in device_groups.items():
                if len(device_alerts) >= 2:  # At least 2 alerts to form an incident
                    # Get device info
                    device = await db.devices.find_one({"_id": ObjectId(device_id)})
                    device_name = device.get("name", "Unknown Device") if device else "Unknown Device"
                    
                    # Calculate severity
                    severities = [a.get("severity", "medium") for a in device_alerts]
                    incident_severity = IncidentCorrelator.calculate_incident_severity(severities)
                    
                    # Get time range
                    created_times = []
                    for a in device_alerts:
                        created_at = a.get("createdAt") or a.get("created_at")
                        if created_at:
                            created_times.append(created_at)
                    
                    correlated_groups.append({
                        "device_id": device_id,
                        "device_name": device_name,
                        "alert_ids": [str(a["_id"]) for a in device_alerts],
                        "alert_count": len(device_alerts),
                        "severity": incident_severity,
                        "first_alert_time": min(created_times) if created_times else datetime.utcnow(),
                        "last_alert_time": max(created_times) if created_times else datetime.utcnow(),
                        "suggested_title": f"Multiple alerts on {device_name}",
                        "suggested_description": f"{len(device_alerts)} alerts detected on {device_name} within {time_window_minutes} minutes"
                    })
        else:
            # Group by time window only
            # Sort alerts by time
            sorted_alerts = sorted(
                alerts,
                key=lambda a: a.get("createdAt") or a.get("created_at") or datetime.utcnow()
            )
            
            # Group consecutive alerts within time window
            current_group = []
            for alert in sorted_alerts:
                if not current_group:
                    current_group = [alert]
                else:
                    # Check if alert is within time window of last alert in group
                    last_alert_time = current_group[-1].get("createdAt") or current_group[-1].get("created_at")
                    alert_time = alert.get("createdAt") or alert.get("created_at")
                    
                    if last_alert_time and alert_time:
                        time_diff = (alert_time - last_alert_time).total_seconds() / 60
                        if time_diff <= time_window_minutes:
                            current_group.append(alert)
                        else:
                            # Save current group and start new one
                            if len(current_group) >= 2:
                                severities = [a.get("severity", "medium") for a in current_group]
                                incident_severity = IncidentCorrelator.calculate_incident_severity(severities)
                                
                                correlated_groups.append({
                                    "alert_ids": [str(a["_id"]) for a in current_group],
                                    "alert_count": len(current_group),
                                    "severity": incident_severity,
                                    "first_alert_time": current_group[0].get("createdAt") or current_group[0].get("created_at"),
                                    "last_alert_time": current_group[-1].get("createdAt") or current_group[-1].get("created_at"),
                                    "suggested_title": f"Multiple alerts detected",
                                    "suggested_description": f"{len(current_group)} alerts detected within {time_window_minutes} minutes"
                                })
                            current_group = [alert]
            
            # Don't forget the last group
            if len(current_group) >= 2:
                severities = [a.get("severity", "medium") for a in current_group]
                incident_severity = IncidentCorrelator.calculate_incident_severity(severities)
                
                correlated_groups.append({
                    "alert_ids": [str(a["_id"]) for a in current_group],
                    "alert_count": len(current_group),
                    "severity": incident_severity,
                    "first_alert_time": current_group[0].get("createdAt") or current_group[0].get("created_at"),
                    "last_alert_time": current_group[-1].get("createdAt") or current_group[-1].get("created_at"),
                    "suggested_title": f"Multiple alerts detected",
                    "suggested_description": f"{len(current_group)} alerts detected within {time_window_minutes} minutes"
                })
        
        return correlated_groups
