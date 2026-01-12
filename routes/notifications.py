"""
routes/notifications.py - Notification preferences endpoints

These let each user control which channels are enabled and what destinations to use.
"""

from datetime import datetime

from fastapi import APIRouter, Depends

from database import get_database
from models import NotificationPreferences, NotificationPreferencesResponse
from routes.auth import get_current_user


router = APIRouter()


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(current_user=Depends(get_current_user)):
    db = await get_database()
    user_id = str(current_user["_id"])

    doc = await db.notification_preferences.find_one({"userId": user_id})
    if not doc:
        # Default preferences: email enabled, destination = user's email
        prefs = NotificationPreferences(email=str(current_user.get("email")))
        now = datetime.utcnow()
        await db.notification_preferences.insert_one(
            {"userId": user_id, "prefs": prefs.model_dump(), "updatedAt": now}
        )
        return NotificationPreferencesResponse(user_id=user_id, updated_at=now, **prefs.model_dump())

    prefs = NotificationPreferences(**doc.get("prefs", {}))
    return NotificationPreferencesResponse(
        user_id=user_id, updated_at=doc.get("updatedAt", datetime.utcnow()), **prefs.model_dump()
    )


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def set_preferences(body: NotificationPreferences, current_user=Depends(get_current_user)):
    db = await get_database()
    user_id = str(current_user["_id"])

    # If email destination not provided, default to account email
    data = body.model_dump()
    if not data.get("email"):
        data["email"] = str(current_user.get("email"))

    now = datetime.utcnow()
    await db.notification_preferences.update_one(
        {"userId": user_id},
        {"$set": {"prefs": data, "updatedAt": now}},
        upsert=True,
    )

    return NotificationPreferencesResponse(user_id=user_id, updated_at=now, **data)

