# routes/notification_preferences.py - User Notification Preferences
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from bson import ObjectId

from models import NotificationPreferences, NotificationPreferencesResponse
from services.notification_service import get_notification_service, NotificationResult
from routes.auth import get_current_user
from database import get_database

router = APIRouter()

DEFAULT_PREFS = {
    "emailEnabled": True,
    "smsEnabled": False,
    "whatsappEnabled": False,
    "voiceEnabled": False,
    "emailSeverities": ["low", "medium", "high", "critical"],
    "smsSeverities": ["high", "critical"],
    "whatsappSeverities": ["medium", "high", "critical"],
    "voiceSeverities": ["critical"],
    "phoneNumber": None,
    "whatsappNumber": None,
    "quietHoursEnabled": False,
    "quietHoursStart": None,
    "quietHoursEnd": None,
    "escalationEnabled": True,
    "escalationDelayMinutes": 15,
}

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


@router.post("/test/{channel}")
async def test_notification_channel(
    channel: str,
    current_user = Depends(get_current_user)
):
    """
    Send a test notification for a specific channel.
    Channels: email, sms, whatsapp, voice
    """
    channel = channel.lower().strip()
    allowed = {"email", "sms", "whatsapp", "voice"}
    if channel not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel")

    db = await get_database()
    user_id = str(current_user["_id"])
    prefs = await db.notification_preferences.find_one({"userId": ObjectId(user_id)}) or DEFAULT_PREFS

    enabled_map = {
        "email": "emailEnabled",
        "sms": "smsEnabled",
        "whatsapp": "whatsappEnabled",
        "voice": "voiceEnabled",
    }
    if not prefs.get(enabled_map[channel], False):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{channel} notifications are disabled")

    service = get_notification_service()
    result: NotificationResult

    if channel == "email":
        subject = "Test notification — IoT Security Platform"
        message = "This is a test email notification from your IoT Security Platform settings."
        success = await service._send_email(
            to_email=current_user.get("email", ""),
            subject=subject,
            message=message,
            severity="medium",
            alert_id="test-notification"
        )
        result = NotificationResult(success, "email", "Sent" if success else "Failed")
    elif channel == "sms":
        phone_number = prefs.get("phoneNumber")
        if not phone_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required for SMS")
        result = service.send_sms(phone_number, "Test SMS from IoT Security Platform.")
    elif channel == "whatsapp":
        whatsapp_number = prefs.get("whatsappNumber")
        if not whatsapp_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WhatsApp number is required")
        result = service.send_whatsapp(whatsapp_number, "Test WhatsApp message from IoT Security Platform.")
    else:
        phone_number = prefs.get("phoneNumber")
        if not phone_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required for voice calls")
        twiml = "<Response><Say>This is a test call from IoT Security Platform.</Say></Response>"
        result = service.make_voice_call(phone_number, twiml)

    return {"ok": result.ok, "channel": result.channel, "detail": result.detail}

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
