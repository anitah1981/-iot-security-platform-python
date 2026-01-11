# routes/notification_preferences.py - User Notification Preferences
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from bson import ObjectId

from models import NotificationPreferences, NotificationPreferencesResponse
from routes.auth import get_current_user
from database import get_database

router = APIRouter()

@router.get("/", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(current_user = Depends(get_current_user)):
    """
    Get current user's notification preferences
    Returns default preferences if none exist
    """
    db = await get_database()
    user_id = str(current_user["_id"])
    
    # Try to find existing preferences
    prefs = await db.notification_preferences.find_one({"userId": ObjectId(user_id)})
    
    if not prefs:
        # Return default preferences
        return NotificationPreferencesResponse(
            user_id=user_id,
            email_enabled=True,
            sms_enabled=False,
            whatsapp_enabled=False,
            voice_enabled=False,
            email_severities=["low", "medium", "high", "critical"],
            sms_severities=["high", "critical"],
            whatsapp_severities=["medium", "high", "critical"],
            voice_severities=["critical"],
            phone_number=None,
            whatsapp_number=None,
            quiet_hours_enabled=False,
            quiet_hours_start=None,
            quiet_hours_end=None,
            escalation_enabled=True,
            escalation_delay_minutes=15,
            updated_at=datetime.utcnow()
        )
    
    # Return existing preferences
    return NotificationPreferencesResponse(
        user_id=user_id,
        email_enabled=prefs.get("emailEnabled", True),
        sms_enabled=prefs.get("smsEnabled", False),
        whatsapp_enabled=prefs.get("whatsappEnabled", False),
        voice_enabled=prefs.get("voiceEnabled", False),
        email_severities=prefs.get("emailSeverities", ["low", "medium", "high", "critical"]),
        sms_severities=prefs.get("smsSeverities", ["high", "critical"]),
        whatsapp_severities=prefs.get("whatsappSeverities", ["medium", "high", "critical"]),
        voice_severities=prefs.get("voiceSeverities", ["critical"]),
        phone_number=prefs.get("phoneNumber"),
        whatsapp_number=prefs.get("whatsappNumber"),
        quiet_hours_enabled=prefs.get("quietHoursEnabled", False),
        quiet_hours_start=prefs.get("quietHoursStart"),
        quiet_hours_end=prefs.get("quietHoursEnd"),
        escalation_enabled=prefs.get("escalationEnabled", True),
        escalation_delay_minutes=prefs.get("escalationDelayMinutes", 15),
        updated_at=prefs.get("updatedAt", datetime.utcnow())
    )

@router.put("/", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user = Depends(get_current_user)
):
    """
    Update user's notification preferences
    Creates new preferences if they don't exist
    """
    db = await get_database()
    user_id = ObjectId(current_user["_id"])
    
    # Build preferences document
    prefs_doc = {
        "userId": user_id,
        "emailEnabled": preferences.email_enabled,
        "smsEnabled": preferences.sms_enabled,
        "whatsappEnabled": preferences.whatsapp_enabled,
        "voiceEnabled": preferences.voice_enabled,
        "emailSeverities": preferences.email_severities,
        "smsSeverities": preferences.sms_severities,
        "whatsappSeverities": preferences.whatsapp_severities,
        "voiceSeverities": preferences.voice_severities,
        "phoneNumber": preferences.phone_number,
        "whatsappNumber": preferences.whatsapp_number,
        "quietHoursEnabled": preferences.quiet_hours_enabled,
        "quietHoursStart": preferences.quiet_hours_start,
        "quietHoursEnd": preferences.quiet_hours_end,
        "escalationEnabled": preferences.escalation_enabled,
        "escalationDelayMinutes": preferences.escalation_delay_minutes,
        "updatedAt": datetime.utcnow()
    }
    
    # Upsert (update or insert)
    await db.notification_preferences.update_one(
        {"userId": user_id},
        {"$set": prefs_doc},
        upsert=True
    )
    
    return NotificationPreferencesResponse(
        user_id=str(user_id),
        **preferences.dict(),
        updated_at=prefs_doc["updatedAt"]
    )
