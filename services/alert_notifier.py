"""
services/alert_notifier.py - Connect alerts -> multi-channel notifications

MVP behavior:
- Determine recipients based on device.organization if present, otherwise notify all users.
- Read each user's NotificationPreferences.
- Send channels based on alert severity + enabled prefs.
- For critical alerts, run a simple escalation timeline if not resolved:
  - 0m: email
  - 2m: sms
  - 5m: whatsapp
  - 10m: voice

Note: Escalation is in-memory (lost on restart). Good enough for MVP; can be moved to a job queue later.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

import anyio
from bson import ObjectId

from database import get_database
from models import NotificationPreferences
from services.notification_service import NotificationService


async def _log_attempt(
    alert_id: ObjectId, user_id: str, channel: str, ok: bool, detail: str
) -> None:
    db = await get_database()
    await db.notification_logs.insert_one(
        {
            "alertId": alert_id,
            "userId": user_id,
            "channel": channel,
            "ok": ok,
            "detail": detail,
            "createdAt": datetime.utcnow(),
        }
    )


def _format_subject(alert: Dict[str, Any], device: Optional[Dict[str, Any]] = None) -> str:
    sev = str(alert.get("severity", "alert")).upper()
    typ = alert.get("type", "system")
    dev_name = (device or {}).get("name") or "Device"
    return f"[{sev}] {typ} — {dev_name}"


def _format_body(alert: Dict[str, Any], device: Optional[Dict[str, Any]] = None) -> str:
    dev = device or {}
    lines = [
        "IoT Security Platform Alert",
        "--------------------------",
        f"Severity: {alert.get('severity')}",
        f"Type: {alert.get('type')}",
        f"Message: {alert.get('message')}",
        "",
        "Device",
        f"- Name: {dev.get('name')}",
        f"- Logical ID: {dev.get('deviceId')}",
        f"- IP: {dev.get('ipAddress')}",
        f"- Status: {dev.get('status')}",
        "",
        f"Time (UTC): {alert.get('createdAt')}",
    ]
    return "\n".join([str(x) for x in lines if x is not None])


def _severity_channels(severity: str) -> list[str]:
    s = (severity or "").lower()
    if s == "low":
        return ["email"]
    if s == "medium":
        return ["email", "sms"]
    if s == "high":
        return ["email", "sms", "whatsapp"]
    if s == "critical":
        return ["email", "sms", "whatsapp", "voice"]
    return ["email"]


async def _get_prefs_for_user(user: Dict[str, Any]) -> NotificationPreferences:
    db = await get_database()
    user_id = str(user["_id"])

    doc = await db.notification_preferences.find_one({"userId": user_id})
    if not doc:
        prefs = NotificationPreferences(email=str(user.get("email")))
        await db.notification_preferences.insert_one(
            {"userId": user_id, "prefs": prefs.model_dump(), "updatedAt": datetime.utcnow()}
        )
        return prefs

    return NotificationPreferences(**doc.get("prefs", {}))


async def _recipients_for_device(device: Optional[Dict[str, Any]]) -> list[Dict[str, Any]]:
    db = await get_database()
    if device and device.get("organization"):
        org = device["organization"]
        # user documents store organization as string in current auth flow
        return await db.users.find({"organization": str(org)}).to_list(length=None)
    return await db.users.find({}).to_list(length=None)


async def _send_channel(
    svc: NotificationService,
    channel: str,
    prefs: NotificationPreferences,
    subject: str,
    body: str,
) -> tuple[bool, str]:
    """
    Run blocking providers in a thread to avoid blocking the event loop.
    Returns (ok, detail).
    """
    if channel == "email":
        if not prefs.email_enabled or not prefs.email:
            return False, "Email disabled or missing destination"
        res = await anyio.to_thread.run_sync(svc.send_email, str(prefs.email), subject, body)
        return res.ok, res.detail

    if channel == "sms":
        if not prefs.sms_enabled or not prefs.phone_number:
            return False, "SMS disabled or missing destination"
        res = await anyio.to_thread.run_sync(svc.send_sms, prefs.phone_number, body)
        return res.ok, res.detail

    if channel == "whatsapp":
        if not prefs.whatsapp_enabled or not prefs.whatsapp_number:
            return False, "WhatsApp disabled or missing destination"
        res = await anyio.to_thread.run_sync(svc.send_whatsapp, prefs.whatsapp_number, body)
        return res.ok, res.detail

    if channel == "voice":
        if not prefs.voice_enabled or not prefs.voice_number:
            return False, "Voice disabled or missing destination"
        res = await anyio.to_thread.run_sync(svc.make_voice_call, prefs.voice_number)
        return res.ok, res.detail

    return False, f"Unknown channel: {channel}"


async def _is_resolved(alert_id: ObjectId) -> bool:
    db = await get_database()
    doc = await db.alerts.find_one({"_id": alert_id}, {"resolved": 1})
    return bool(doc and doc.get("resolved"))


async def _run_escalation(alert_id: ObjectId, user: Dict[str, Any], device: Optional[Dict[str, Any]]) -> None:
    """
    Critical escalation (best-effort).
    Stops if the alert is resolved.
    """
    svc = NotificationService()
    prefs = await _get_prefs_for_user(user)

    # If escalation disabled, just send based on the normal mapping.
    if not prefs.escalation_enabled:
        return

    db = await get_database()
    alert = await db.alerts.find_one({"_id": alert_id})
    if not alert:
        return

    subject = _format_subject(alert, device=device)
    body = _format_body(alert, device=device)

    timeline = [
        (0, "email"),
        (2 * 60, "sms"),
        (5 * 60, "whatsapp"),
        (10 * 60, "voice"),
    ]

    for delay_s, channel in timeline:
        if delay_s:
            await asyncio.sleep(delay_s)
        if await _is_resolved(alert_id):
            return

        ok, detail = await _send_channel(svc, channel, prefs, subject, body)
        await _log_attempt(alert_id, str(user["_id"]), channel, ok, detail)


async def notify_alert(alert_id: ObjectId) -> None:
    """
    Notify recipients for an alert (best-effort).
    Safe to call from routes or background tasks.
    """
    db = await get_database()
    alert = await db.alerts.find_one({"_id": alert_id})
    if not alert:
        return

    device = None
    if alert.get("deviceId"):
        device = await db.devices.find_one({"_id": alert["deviceId"]})

    recipients = await _recipients_for_device(device)
    if not recipients:
        return

    svc = NotificationService()
    subject = _format_subject(alert, device=device)
    body = _format_body(alert, device=device)
    channels = _severity_channels(str(alert.get("severity", "low")))

    for user in recipients:
        prefs = await _get_prefs_for_user(user)

        # Critical alerts: use escalation timeline
        if str(alert.get("severity", "")).lower() == "critical":
            asyncio.create_task(_run_escalation(alert_id, user, device))
            continue

        # Non-critical: send mapped channels immediately
        for ch in channels:
            ok, detail = await _send_channel(svc, ch, prefs, subject, body)
            await _log_attempt(alert_id, str(user["_id"]), ch, ok, detail)

