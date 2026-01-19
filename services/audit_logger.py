# services/audit_logger.py - Audit Logging Service
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class AuditLogger:
    """Service for logging user actions for compliance and security"""
    
    @staticmethod
    async def log(
        db,
        user_id: ObjectId,
        user_email: str,
        user_name: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log an audit event
        
        Args:
            db: Database connection
            user_id: User performing the action
            user_email: User's email
            user_name: User's name
            action: Action performed (e.g., "login", "device_create", "alert_resolve")
            resource_type: Type of resource (e.g., "user", "device", "alert")
            resource_id: ID of the affected resource
            details: Additional context
            ip_address: User's IP address
            user_agent: User's browser/client
        """
        log_entry = {
            "user_id": user_id,
            "user_email": user_email,
            "user_name": user_name,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow()
        }
        
        try:
            await db.audit_logs.insert_one(log_entry)
        except Exception as e:
            print(f"Failed to write audit log: {e}")
            # Don't fail the main operation if audit logging fails
    
    @staticmethod
    async def log_login(db, user_id: ObjectId, user_email: str, user_name: str, ip_address: Optional[str] = None):
        """Log user login"""
        await AuditLogger.log(
            db=db,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            action="login",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=ip_address
        )
    
    @staticmethod
    async def log_logout(db, user_id: ObjectId, user_email: str, user_name: str):
        """Log user logout"""
        await AuditLogger.log(
            db=db,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            action="logout",
            resource_type="user",
            resource_id=str(user_id)
        )
    
    @staticmethod
    async def log_device_created(
        db,
        user_id: ObjectId,
        user_email: str,
        user_name: str,
        device_id: str,
        device_name: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log device creation"""
        await AuditLogger.log(
            db=db,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            action="device_create",
            resource_type="device",
            resource_id=device_id,
            details={"device_name": device_name},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    async def log_device_deleted(
        db,
        user_id: ObjectId,
        user_email: str,
        user_name: str,
        device_id: str,
        device_name: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log device deletion"""
        await AuditLogger.log(
            db=db,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            action="device_delete",
            resource_type="device",
            resource_id=device_id,
            details={"device_name": device_name},
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    async def log_device_updated(
        db,
        user_id: ObjectId,
        user_email: str,
        user_name: str,
        device_id: str,
        device_name: str,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log device update"""
        await AuditLogger.log(
            db=db,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            action="device_update",
            resource_type="device",
            resource_id=device_id,
            details={"device_name": device_name, "changes": changes or {}},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    async def log_alert_resolved(db, user_id: ObjectId, user_email: str, user_name: str, alert_id: str, alert_severity: str):
        """Log alert resolution"""
        await AuditLogger.log(
            db=db,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            action="alert_resolve",
            resource_type="alert",
            resource_id=alert_id,
            details={"severity": alert_severity}
        )
    
    @staticmethod
    async def log_settings_changed(db, user_id: ObjectId, user_email: str, user_name: str, settings_type: str):
        """Log settings change"""
        await AuditLogger.log(
            db=db,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            action="settings_update",
            resource_type="settings",
            details={"settings_type": settings_type}
        )
    
    @staticmethod
    async def log_subscription_changed(db, user_id: ObjectId, user_email: str, user_name: str, old_plan: str, new_plan: str):
        """Log subscription change"""
        await AuditLogger.log(
            db=db,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            action="subscription_update",
            resource_type="subscription",
            details={"old_plan": old_plan, "new_plan": new_plan}
        )
