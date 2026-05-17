"""
Agent Security Report - receives DNS change and unknown device alerts from the device agent.
Uses X-API-Key (same as heartbeat) to associate alerts with the user's account.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Request

from database import get_database
from services.device_agent_key_service import get_user_by_api_key
from services.notification_service import send_alert_notification

router = APIRouter()


DEFAULT_NOTIFICATION_PREFS = {
    "emailEnabled": True,
    "smsEnabled": False,
    "whatsappEnabled": False,
    "voiceEnabled": False,
    "emailSeverities": ["low", "medium", "high", "critical"],
    "smsSeverities": ["high", "critical"],
    "whatsappSeverities": ["medium", "high", "critical"],
    "voiceSeverities": ["critical"],
}


async def _agent_api_key_user(request: Request):
    raw = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not raw:
        return None
    return await get_user_by_api_key(raw)


async def _send_agent_alert_notification(db, user: dict, device_id, alert_doc: dict, alert_id: str) -> None:
    """Notify the API-key owner about security findings without failing report ingestion."""
    try:
        device = await db.devices.find_one({"_id": device_id})
        prefs = await db.notification_preferences.find_one({"userId": user["_id"]}) or DEFAULT_NOTIFICATION_PREFS
        await send_alert_notification(
            user_email=user.get("email", ""),
            user_name=user.get("name", "User"),
            device_name=(device or {}).get("name", "Network Watchdog"),
            alert_message=alert_doc["message"],
            alert_severity=alert_doc.get("severity", "high"),
            notification_prefs=prefs,
            alert_id=alert_id,
        )
    except Exception as exc:
        print(f"[AGENT SECURITY] Failed to send alert notification: {exc}")


@router.post("/security-report")
async def receive_security_report(
    request: Request,
    api_key_user: Optional[dict] = Depends(_agent_api_key_user),
):
    """
    Receive security report from device agent (DNS change, unknown devices on network).
    Requires X-API-Key header (device agent API key from Settings).
    """
    if not api_key_user:
        return {"ok": False, "error": "Invalid or missing X-API-Key"}

    body = await request.json()
    dns_changed = body.get("dns_changed", False)
    dns_servers = body.get("dns_servers") or []
    expected_dns = body.get("expected_dns") or []
    unknown_ips = body.get("unknown_ips") or []

    db = await get_database()
    now = datetime.utcnow()
    user_id = api_key_user["_id"]
    family_id = api_key_user.get("_family_id")

    device_filter = {"family_id": family_id} if family_id else {"$or": [{"userId": user_id}, {"user_id": user_id}]}
    devices = await db.devices.find(device_filter).limit(1).to_list(length=1)
    device_id = devices[0]["_id"] if devices else None

    if not device_id:
        result = await db.devices.insert_one(
            {
                "deviceId": "agent-watchdog",
                "name": "Network Watchdog",
                "type": "Agent",
                "userId": user_id,
                "user_id": user_id,
                "family_id": family_id,
                "status": "online",
                "createdAt": now,
                "updatedAt": now,
            }
        )
        device_id = result.inserted_id

    alerts_created = []

    if dns_changed and expected_dns:
        recent = await db.alerts.find_one(
            {
                "deviceId": device_id,
                "message": {"$regex": "DNS server"},
                "createdAt": {"$gte": now - timedelta(hours=1)},
            }
        )
        if not recent:
            alert_doc = {
                "deviceId": device_id,
                "message": f"DNS server changed: expected {expected_dns}, got {dns_servers}",
                "severity": "high",
                "type": "security",
                "context": {"expected_dns": expected_dns, "current_dns": dns_servers, "change_type": "dns_server"},
                "resolved": False,
                "resolvedAt": None,
                "createdAt": now,
                "updatedAt": now,
            }
            result = await db.alerts.insert_one(alert_doc)
            alerts_created.append(str(result.inserted_id))
            await _send_agent_alert_notification(db, api_key_user, device_id, alert_doc, str(result.inserted_id))

    if unknown_ips:
        recent = await db.alerts.find_one(
            {
                "deviceId": device_id,
                "message": {"$regex": "Unknown device"},
                "createdAt": {"$gte": now - timedelta(hours=6)},
            }
        )
        if not recent:
            ips_str = ", ".join(unknown_ips[:5])
            if len(unknown_ips) > 5:
                ips_str += f" and {len(unknown_ips) - 5} more"
            alert_doc = {
                "deviceId": device_id,
                "message": f"Unknown device(s) detected on network: {ips_str}",
                "severity": "high",
                "type": "security",
                "context": {"unknown_ips": unknown_ips[:20], "change_type": "unknown_device"},
                "resolved": False,
                "resolvedAt": None,
                "createdAt": now,
                "updatedAt": now,
            }
            result = await db.alerts.insert_one(alert_doc)
            alerts_created.append(str(result.inserted_id))
            await _send_agent_alert_notification(db, api_key_user, device_id, alert_doc, str(result.inserted_id))

    return {"ok": True, "alerts_created": alerts_created}
