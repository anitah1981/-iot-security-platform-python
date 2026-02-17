# routes/notification_preferences.py - User Notification Preferences
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime
from bson import ObjectId

from models import NotificationPreferences, NotificationPreferencesResponse, NotificationPreferencesSaveResponse
from services.notification_service import get_notification_service, NotificationResult
from routes.auth import get_current_user
from database import get_database
from services.audit_logger import AuditLogger

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


def _is_valid_e164(value: str) -> bool:
    """Basic E.164 validation (+ followed by 8-15 digits)."""
    value = value.strip()
    if not value.startswith("+"):
        return False
    digits = value[1:]
    return digits.isdigit() and 8 <= len(digits) <= 15


async def _send_verification_to_all_channels(
    current_user: dict,
    preferences: NotificationPreferences,
    service,
) -> tuple[dict, list]:
    """
    Send a one-off verification to each enabled channel so the user can confirm
    their details are correct. No further action required from the consumer.
    Returns (verification_sent: {channel: bool}, verification_failed: [{channel, message}]).
    """
    verification_sent = {"email": False, "sms": False, "whatsapp": False, "voice": False}
    verification_failed = []
    user_email = (current_user.get("email") or "").strip()
    phone = (preferences.phone_number or "").strip() or None
    whatsapp_number = (preferences.whatsapp_number or "").strip() or None

    # Email
    if preferences.email_enabled and user_email:
        try:
            ok = await service._send_email(
                to_email=user_email,
                subject="Alert-Pro – your email is set up",
                message="This is a verification. Your email is set up correctly. You'll receive alerts here when a device goes offline.",
                severity="low",
                alert_id="verification",
            )
            verification_sent["email"] = ok
            if not ok:
                verification_failed.append({"channel": "email", "message": "We couldn't send a verification email. Please check your address and try again."})
        except Exception as e:
            print(f"[VERIFY] Email failed: {e}")
            verification_failed.append({"channel": "email", "message": "We couldn't send a verification email. Please check your address and try again."})

    # SMS
    if preferences.sms_enabled and phone:
        result = service.send_sms(phone, "Alert-Pro: Your number is set up correctly. You'll receive alerts here when a device goes offline.")
        verification_sent["sms"] = result.ok
        if not result.ok:
            verification_failed.append({"channel": "sms", "message": "We couldn't send a verification text. Please check your number and try again."})

    # WhatsApp
    if preferences.whatsapp_enabled and whatsapp_number:
        result = service.send_whatsapp(whatsapp_number, "Alert-Pro: Your number is set up correctly. You'll receive alerts here when a device goes offline.")
        verification_sent["whatsapp"] = result.ok
        if not result.ok:
            verification_failed.append({"channel": "whatsapp", "message": "We couldn't send a verification to WhatsApp. Please check the number and try again."})

    # Voice
    if preferences.voice_enabled and phone:
        twiml = "<Response><Say>This is a verification call from Alert-Pro. Your number is set up correctly. You will receive alert calls here when a device goes offline.</Say></Response>"
        result = service.make_voice_call(phone, twiml)
        verification_sent["voice"] = result.ok
        if not result.ok:
            verification_failed.append({"channel": "voice", "message": "We couldn't place a verification call. Please check your number and try again."})

    return verification_sent, verification_failed

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


@router.post("/test-offline-alert")
async def test_offline_alert(current_user=Depends(get_current_user)):
    """
    Trigger the exact same notification flow as when a device goes offline.
    Use this to test that SMS, WhatsApp, and Voice actually reach you without turning WiFi off.
    """
    from services.notification_service import send_alert_notification
    db = await get_database()
    user_id = ObjectId(current_user["_id"])
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    prefs_doc = await db.notification_preferences.find_one({"userId": user_id})
    notif_prefs = {**DEFAULT_PREFS}
    if prefs_doc:
        for k, v in prefs_doc.items():
            if k in DEFAULT_PREFS and v is not None:
                if k in ("emailEnabled", "smsEnabled", "whatsappEnabled", "voiceEnabled", "quietHoursEnabled", "escalationEnabled"):
                    notif_prefs[k] = v in (True, "true", "1", 1, "yes", "on")
                else:
                    notif_prefs[k] = v
    device_name = "Test Device"
    message = "Test offline alert – if you receive this, notifications work."
    results = await send_alert_notification(
        user_email=user.get("email", ""),
        user_name=user.get("name", "User"),
        device_name=device_name,
        alert_message=message,
        alert_severity="critical",
        notification_prefs=notif_prefs,
        alert_id="test-offline-alert",
    )
    return {
        "ok": True,
        "message": "Test offline alert sent. Check your phone/SMS/WhatsApp/email.",
        "results": [{"channel": r.channel, "ok": r.ok, "detail": r.detail} for r in results],
    }


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
        subject = "Test notification — Alert-Pro"
        message = "This is a test email notification from your Alert-Pro settings."
        success = await service._send_email(
            to_email=current_user.get("email", ""),
            subject=subject,
            message=message,
            severity="medium",
            alert_id="test-notification"
        )
        result = NotificationResult(success, "email", "Sent" if success else "Failed")
    elif channel == "sms":
        if not service.sms_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS is disabled. Configure Twilio (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER) in .env, or set SMS_ENABLED=true to enable."
            )
        phone_number = prefs.get("phoneNumber")
        if not phone_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required for SMS")
        result = service.send_sms(phone_number, "Test SMS from Alert-Pro.")
    elif channel == "whatsapp":
        whatsapp_number = prefs.get("whatsappNumber")
        if not whatsapp_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WhatsApp number is required")
        result = service.send_whatsapp(whatsapp_number, "Test WhatsApp message from Alert-Pro.")
    else:
        phone_number = prefs.get("phoneNumber")
        if not phone_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required for voice calls")
        twiml = "<Response><Say>This is a test call from Alert-Pro.</Say></Response>"
        result = service.make_voice_call(phone_number, twiml)

    return {
        "ok": result.ok,
        "channel": result.channel,
        "detail": result.detail,
        "error_code": result.error_code,
    }

@router.put("/", response_model=NotificationPreferencesSaveResponse)
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
    service = get_notification_service()

    if preferences.sms_enabled and not service.sms_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMS is not available right now. Please use another channel or try again later."
        )

    if (preferences.sms_enabled or preferences.voice_enabled) and not preferences.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required for SMS or voice notifications"
        )
    if preferences.phone_number and not _is_valid_e164(preferences.phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must be in E.164 format (e.g., +44123456789)"
        )
    if preferences.whatsapp_enabled and not preferences.whatsapp_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WhatsApp number is required for WhatsApp notifications"
        )
    if preferences.whatsapp_number and not _is_valid_e164(preferences.whatsapp_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WhatsApp number must be in E.164 format (e.g., +44123456789)"
        )
    
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
    
    # Log notification preferences change
    try:
        user = await db.users.find_one({"_id": user_id})
        await AuditLogger.log(
            db=db,
            user_id=user_id,
            user_email=user.get("email", "") if user else current_user.get("email", ""),
            user_name=user.get("name", "") if user else current_user.get("name", ""),
            action="notification_preferences_update",
            resource_type="settings",
            resource_id=str(user_id),
            details={
                "email_enabled": preferences.email_enabled,
                "sms_enabled": preferences.sms_enabled,
                "whatsapp_enabled": preferences.whatsapp_enabled,
                "voice_enabled": preferences.voice_enabled,
                "quiet_hours_enabled": preferences.quiet_hours_enabled
            }
        )
    except Exception as e:
        print(f"Failed to log notification preferences update: {e}")

    # Automatically send verification to each enabled channel so the user can confirm their details — no further action required.
    service = get_notification_service()
    verification_sent = {}
    verification_failed = []
    try:
        verification_sent, verification_failed = await _send_verification_to_all_channels(current_user, preferences, service)
    except Exception as e:
        print(f"[VERIFY] Verification send error: {e}")
        verification_failed.append({"channel": "all", "message": "We couldn't send all verifications. Please try again in a moment."})

    return NotificationPreferencesSaveResponse(
        user_id=str(user_id),
        **preferences.dict(),
        updated_at=prefs_doc["updatedAt"],
        verification_sent=verification_sent,
        verification_failed=verification_failed,
    )
