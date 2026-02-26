"""
Plan Limits Middleware
Enforces subscription plan limits on devices, alerts, and features
"""

from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime, timedelta

from database import get_database
from services.stripe_service import StripeService


class PlanLimits:
    """Helper class to check and enforce plan limits"""
    
    @staticmethod
    async def check_device_limit(user: dict) -> bool:
        """
        Check if user can add more devices
        
        Args:
            user: User document from database
            
        Returns:
            True if under limit, raises HTTPException if over limit
        """
        plan_name = user.get("plan", "free")
        plan_config = StripeService.get_plan_config(plan_name)
        
        if not plan_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid plan configuration"
            )
        
        device_limit = plan_config["device_limit"]
        
        # Unlimited devices
        if device_limit < 0:
            return True
        
        # Count user's devices (exclude soft-deleted; support both user_id and userId)
        db = await get_database()
        uid = user["_id"]
        device_count = await db.devices.count_documents({
            "$or": [{"user_id": uid}, {"userId": uid}],
            "isDeleted": {"$ne": True}
        })
        
        if device_count >= device_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": f"Device limit reached for {plan_name} plan",
                    "current": device_count,
                    "limit": device_limit,
                    "plan": plan_name,
                    "upgrade_url": "/pricing"
                }
            )
        
        return True
    
    @staticmethod
    async def get_device_count(user: dict) -> dict:
        """
        Get current device count and limit
        
        Args:
            user: User document from database
            
        Returns:
            Dict with current count, limit, and percentage
        """
        plan_name = user.get("plan", "free")
        plan_config = StripeService.get_plan_config(plan_name)
        
        if not plan_config:
            return {"current": 0, "limit": 0, "percentage": 0}
        
        device_limit = plan_config["device_limit"]
        
        # Count user's devices (exclude soft-deleted; support both user_id and userId)
        db = await get_database()
        uid = user["_id"]
        device_count = await db.devices.count_documents({
            "$or": [{"user_id": uid}, {"userId": uid}],
            "isDeleted": {"$ne": True}
        })
        
        if device_limit < 0:
            return {
                "current": device_count,
                "limit": "unlimited",
                "percentage": 0
            }
        
        percentage = (device_count / device_limit * 100) if device_limit > 0 else 0
        
        return {
            "current": device_count,
            "limit": device_limit,
            "percentage": percentage
        }
    
    @staticmethod
    async def cleanup_old_alerts(user: dict) -> int:
        """
        Clean up alerts older than plan retention period
        
        Args:
            user: User document from database
            
        Returns:
            Number of alerts deleted
        """
        plan_name = user.get("plan", "free")
        plan_config = StripeService.get_plan_config(plan_name)
        
        if not plan_config:
            return 0
        
        retention_days = plan_config["history_days"]
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Delete old alerts (support both user_id/userId and created_at/createdAt)
        db = await get_database()
        uid = user["_id"]
        result = await db.alerts.delete_many({
            "$and": [
                {"$or": [{"user_id": uid}, {"userId": uid}]},
                {"$or": [{"created_at": {"$lt": cutoff_date}}, {"createdAt": {"$lt": cutoff_date}}]}
            ]
        })
        
        return result.deleted_count
    
    @staticmethod
    async def check_feature_access(user: dict, feature: str) -> bool:
        """
        Check if user's plan includes a specific feature
        
        Args:
            user: User document from database
            feature: Feature name to check
            
        Returns:
            True if feature is available, raises HTTPException if not
        """
        plan_name = user.get("plan", "free")
        
        # Feature access by plan
        FEATURE_PLANS = {
            "alert_exports": ["pro", "business"],
            "teams": ["business"],
            "audit_logs": ["business"],
            "api_access": ["business"],
            "advanced_analytics": ["pro", "business"],
            "scheduled_exports": ["business"],
            "incident_timeline": ["pro", "business"],
            "device_grouping": ["pro", "business"],
            "sms_notifications": ["pro", "business"],
            "whatsapp_notifications": ["pro", "business"],
            "voice_notifications": ["pro", "business"]
        }
        
        required_plans = FEATURE_PLANS.get(feature, [])
        
        if required_plans and plan_name not in required_plans:
            min_plan = required_plans[0]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": f"This feature requires {min_plan} plan or higher",
                    "feature": feature,
                    "current_plan": plan_name,
                    "required_plan": min_plan,
                    "upgrade_url": "/pricing"
                }
            )
        
        return True
    
    @staticmethod
    def get_rate_limit_by_plan(plan: str) -> int:
        """
        Get API rate limit based on plan
        
        Args:
            plan: Plan name
            
        Returns:
            Requests per minute
        """
        RATE_LIMITS = {
            "free": 60,      # 60 req/min
            "pro": 300,      # 300 req/min
            "business": 1000  # 1000 req/min
        }
        
        return RATE_LIMITS.get(plan, 60)


async def enforce_device_limit(user: dict):
    """
    Dependency to enforce device limit before creating devices
    
    Usage:
        @router.post("/devices", dependencies=[Depends(enforce_device_limit)])
    """
    await PlanLimits.check_device_limit(user)


async def require_feature(feature: str):
    """
    Dependency factory to require specific features
    
    Usage:
        @router.get("/export", dependencies=[Depends(require_feature("alert_exports"))])
    """
    async def check(user: dict):
        await PlanLimits.check_feature_access(user, feature)
    return check
