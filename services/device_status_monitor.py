"""
services/device_status_monitor.py - Active device status monitoring

Periodically checks device connectivity by:
- Checking ARP table
- Pinging device IPs
- Scanning common ports

When devices go offline:
- Updates device status
- Creates connectivity alerts
- Sends notifications
"""

import asyncio
import socket
import subprocess
import platform
import re
from datetime import datetime, timedelta
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from bson import ObjectId
from database import get_database
from services.notification_service import NotificationService


DEFAULT_CHECK_INTERVAL_SECONDS = 30


def _ping_sync(ip: str, timeout_ms: int = 1500) -> bool:
    """Synchronous ping check."""
    try:
        os_name = platform.system().lower()
        if os_name == "windows":
            cmd = ["ping", "-n", "1", "-w", str(max(500, timeout_ms)), ip]
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=max(3, timeout_ms / 1000 + 1),
                creationflags=subprocess.CREATE_NO_WINDOW if os_name == "windows" else 0
            )
        else:
            cmd = ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), ip]
            result = subprocess.run(cmd, capture_output=True, timeout=max(3, timeout_ms / 1000 + 1))
        return result.returncode == 0
    except:
        return False


def _get_arp_table_sync() -> Dict[str, str]:
    """Get ARP table mapping IP -> MAC."""
    result = {}
    try:
        if platform.system().lower() == "windows":
            out = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
            if out.returncode == 0:
                for line in out.stdout.splitlines():
                    m = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-f-]{17})", line.lower())
                    if m:
                        result[m.group(1)] = m.group(2).replace("-", ":")
        else:
            out = subprocess.run(["arp", "-n"], capture_output=True, text=True, timeout=5)
            if out.returncode != 0:
                out = subprocess.run(["ip", "neigh"], capture_output=True, text=True, timeout=5)
                if out.returncode != 0:
                    return result
                for line in out.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 5 and parts[0].replace(".", "").isdigit():
                        result[parts[0]] = parts[4].lower()
            else:
                for line in out.stdout.splitlines():
                    m = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+ether\s+([0-9a-f:]+)", line)
                    if m:
                        result[m.group(1)] = m.group(2).lower()
    except Exception:
        pass
    return result


# Default notification prefs when user has none saved (matches routes/alerts.py and notification_preferences)
_DEFAULT_NOTIFICATION_PREFS = {
    "emailEnabled": True,
    "smsEnabled": False,
    "whatsappEnabled": False,
    "voiceEnabled": False,
    "emailSeverities": ["low", "medium", "high", "critical"],
    "smsSeverities": ["high", "critical"],
    "whatsappSeverities": ["medium", "high", "critical"],
    "voiceSeverities": ["critical"],
}

# Use critical severity so offline alerts are never suppressed by quiet hours
CONNECTIVITY_ALERT_SEVERITY = "critical"


async def resolve_offline_alerts_for_device(device_mongo_id: ObjectId) -> int:
    """
    Mark all unresolved 'device is offline' connectivity alerts for this device as resolved.
    Call when the device comes back online so the dashboard doesn't show stale offline alerts.
    Returns the number of alerts resolved.
    """
    db = await get_database()
    now = datetime.utcnow()
    result = await db.alerts.update_many(
        {
            "deviceId": device_mongo_id,
            "type": "connectivity",
            "message": {"$regex": r"is offline$"},
            "resolved": False,
        },
        {"$set": {"resolved": True, "resolvedAt": now, "updatedAt": now}},
    )
    if result.modified_count:
        print(f"[MONITOR] Resolved {result.modified_count} offline alert(s) for device {device_mongo_id} (device back online)")
    return result.modified_count


async def _create_connectivity_alert(device_mongo_id: ObjectId, device_name: str, user_id: ObjectId) -> None:
    """Create a connectivity alert for offline device (deduped within 5 minutes)."""
    db = await get_database()
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=5)
    user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id

    message = f"Device '{device_name}' is offline"
    
    existing = await db.alerts.find_one({
        "deviceId": device_mongo_id,
        "type": "connectivity",
        "severity": CONNECTIVITY_ALERT_SEVERITY,
        "createdAt": {"$gte": cutoff},
        "resolved": False
    })
    
    if existing:
        print(f"[NOTIFY] Skipping alert for '{device_name}': already sent in last 5 minutes (dedupe)")
        return  # Already alerted recently

    print(f"[NOTIFY] Creating connectivity alert for '{device_name}' (device_id={device_mongo_id}, user_id={user_id})")
    alert_doc = {
        "deviceId": device_mongo_id,
        "message": message,
        "severity": CONNECTIVITY_ALERT_SEVERITY,
        "type": "connectivity",
        "context": {"reason": "Device not responding to network checks"},
        "resolved": False,
        "resolvedAt": None,
        "createdAt": now,
        "updatedAt": now,
    }
    
    result = await db.alerts.insert_one(alert_doc)
    
    # Send notification: load prefs from notification_preferences collection (not user doc)
    try:
        user = await db.users.find_one({"_id": user_id})
        if not user:
            print(f"[NOTIFY] Skipping: user not found for user_id={user_id}")
            return
        
        prefs_doc = await db.notification_preferences.find_one({"userId": user_id})
        notif_prefs = {**_DEFAULT_NOTIFICATION_PREFS}
        if prefs_doc:
            for k, v in prefs_doc.items():
                if k in _DEFAULT_NOTIFICATION_PREFS and v is not None:
                    # Normalize booleans (DB or API might store "true"/"false" strings)
                    if k in ("emailEnabled", "smsEnabled", "whatsappEnabled", "voiceEnabled", "quietHoursEnabled", "escalationEnabled"):
                        notif_prefs[k] = v in (True, "true", "1", 1, "yes", "on")
                    else:
                        notif_prefs[k] = v
        print(f"[NOTIFY] Sending offline alert for '{device_name}' to {user.get('email')} | sms={notif_prefs.get('smsEnabled')} phone={bool(notif_prefs.get('phoneNumber'))} whatsapp={notif_prefs.get('whatsappEnabled')} wa={bool(notif_prefs.get('whatsappNumber'))} voice={notif_prefs.get('voiceEnabled')}")
        from services.notification_service import send_alert_notification
        
        results = await send_alert_notification(
            user_email=user.get("email", ""),
            user_name=user.get("name", "User"),
            device_name=device_name,
            alert_message=message,
            alert_severity=CONNECTIVITY_ALERT_SEVERITY,
            notification_prefs=notif_prefs,
            alert_id=str(result.inserted_id)
        )
        for r in results:
            print(f"[NOTIFY] Offline alert {device_name} -> {r.channel}: {r.detail}")
            if not r.ok and r.channel in ("sms", "whatsapp", "voice"):
                print(f"[WARNING] {r.channel.upper()} not delivered: {r.detail}. Check Twilio env (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER) and SMS_ENABLED=true for SMS.")
    except Exception as e:
        print(f"[WARNING] Failed to send notification for offline device: {e}")
        import traceback
        traceback.print_exc()


async def check_device_status_once() -> None:
    """
    Check all devices' connectivity status.
    Updates status and creates alerts for devices that go offline.
    """
    db = await get_database()
    now = datetime.utcnow()
    
    # Get all non-deleted devices
    devices = await db.devices.find({"isDeleted": {"$ne": True}}).to_list(length=None)
    
    if not devices:
        return
    
    # Log which devices we're checking (so you can confirm the right device/IP is monitored)
    device_list = [f"{d.get('name', '?')} ({d.get('ipAddress', 'no-ip')})" for d in devices]
    print(f"[MONITOR] Checking {len(devices)} device(s): {', '.join(device_list)}")
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=20)
    
    try:
        async def check_device(device):
            ip = device.get("ipAddress")
            if not ip or ip == "0.0.0.0":
                print(f"[MONITOR] Skipping {device.get('name', '?')}: no valid IP")
                return
            
            # ACTIVELY check if device is reachable (don't trust stale ARP)
            # 1. Try ping first
            is_online = await loop.run_in_executor(executor, _ping_sync, ip, 1500)
            
            # 2. If ping fails, try port scanning (phones often block ping)
            if not is_online:
                test_ports = [80, 443, 8080, 5353, 62078]
                for port in test_ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(0.5)
                        result = sock.connect_ex((ip, port))
                        sock.close()
                        if result == 0:
                            is_online = True
                            break
                    except:
                        pass
            
            # Do NOT use ARP to mark online: ARP entries stay in cache after WiFi is off,
            # so the device would stay "online" when it's actually offline.
            new_status = "online" if is_online else "offline"
            old_status = device.get("status")

            # When server would mark device offline: if we have a very recent heartbeat, trust it.
            # The device agent runs on the user's network and can reach devices; the server often
            # cannot (e.g. cloud or different subnet), so server ping fails and would wrongly
            # mark devices offline. Skip overwriting to offline when lastSeen is recent.
            if new_status == "offline":
                last_seen = device.get("lastSeen")
                heartbeat_interval = int(device.get("heartbeatInterval", 30))
                grace_seconds = max(120, heartbeat_interval * 4)
                if last_seen:
                    try:
                        age_sec = (now - last_seen).total_seconds()
                    except TypeError:
                        age_sec = (now - last_seen.replace(tzinfo=None) if getattr(last_seen, "tzinfo", None) else now - last_seen).total_seconds()
                    if age_sec < grace_seconds:
                        # Agent reported recently; don't overwrite with server's failed ping
                        return
                # No recent lastSeen: allow marking offline (sweep would do it anyway)
            
            # Update if status changed
            if old_status != new_status:
                await db.devices.update_one(
                    {"_id": device["_id"]},
                    {"$set": {
                        "status": new_status,
                        "lastSeen": now if is_online else device.get("lastSeen"),
                        "updatedAt": now
                    }}
                )
                # When device comes back online, resolve any "device is offline" alerts for it
                if new_status == "online":
                    await resolve_offline_alerts_for_device(device["_id"])
                # Create alert if device went offline
                elif new_status == "offline" and device.get("alertsEnabled", True):
                    user_id = device.get("userId") or device.get("user_id")
                    if user_id:
                        print(f"[MONITOR] Device '{device.get('name')}' ({ip}) went OFFLINE -> creating alert and sending notifications")
                        await _create_connectivity_alert(
                            device["_id"],
                            device.get("name", "Unknown Device"),
                            user_id
                        )
                    else:
                        print(f"[WARNING] Device {device.get('name')} ({ip}) has no userId/user_id - skipping offline alert/notifications")
                else:
                    if new_status == "offline" and not device.get("alertsEnabled", True):
                        print(f"[MONITOR] Device {device.get('name')} ({ip}) went offline but alerts disabled for this device")

                print(f"[MONITOR] Device {device.get('name')} ({ip}): {old_status} -> {new_status}")
        
        await asyncio.gather(*[check_device(d) for d in devices], return_exceptions=True)
        
    except Exception as e:
        print(f"[WARNING] Device status monitor error: {e}")
    finally:
        executor.shutdown(wait=False)


async def run_forever(interval_seconds: int = DEFAULT_CHECK_INTERVAL_SECONDS) -> None:
    """Run status checks forever on a fixed interval."""
    print(f"[OK] Device status monitor started (checking every {interval_seconds}s)")
    
    iteration = 0
    while True:
        try:
            iteration += 1
            print(f"[MONITOR] Starting check iteration #{iteration}")
            await check_device_status_once()
            print(f"[MONITOR] Completed check iteration #{iteration}")
        except Exception as e:
            print(f"[WARNING] Device status monitor error: {e}")
            import traceback
            traceback.print_exc()
        await asyncio.sleep(max(5, interval_seconds))


_monitor_task = None

def start_device_status_monitor(interval_seconds: int = DEFAULT_CHECK_INTERVAL_SECONDS) -> None:
    """Fire-and-forget background status monitoring task (call during app startup)."""
    global _monitor_task
    _monitor_task = asyncio.create_task(run_forever(interval_seconds=interval_seconds))
