"""
services/heartbeat_sweep.py - Background device heartbeat monitoring

This periodically checks for devices that haven't checked in recently and:
- marks them offline
- creates a connectivity alert (deduped)

MVP: best-effort background task; safe to run even without external services.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId

from database import get_database


DEFAULT_SWEEP_INTERVAL_SECONDS = 30


async def _create_connectivity_alert_if_needed(device_mongo_id: ObjectId, message: str) -> None:
    """Dedup connectivity alerts within 5 minutes (mirrors routes/alerts.py intent)."""
    db = await get_database()
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=5)

    existing = await db.alerts.find_one(
        {
            "deviceId": device_mongo_id,
            "message": message,
            "type": "connectivity",
            "severity": "high",
            "createdAt": {"$gte": cutoff},
        }
    )
    if existing:
        return

    await db.alerts.insert_one(
        {
            "deviceId": device_mongo_id,
            "message": message,
            "severity": "high",
            "type": "connectivity",
            "context": {},
            "resolved": False,
            "resolvedAt": None,
            "createdAt": now,
            "updatedAt": now,
        }
    )


async def sweep_once() -> None:
    """
    One sweep pass:
    - For each device, consider it offline if lastSeen is older than (2 * heartbeatInterval).
    """
    db = await get_database()
    now = datetime.utcnow()

    cursor = db.devices.find({})
    devices = await cursor.to_list(length=None)

    for d in devices:
        heartbeat_interval = int(d.get("heartbeatInterval", 30))
        last_seen: Optional[datetime] = d.get("lastSeen")

        if not last_seen:
            continue

        offline_after = timedelta(seconds=max(10, heartbeat_interval * 2))
        should_be_offline = now - last_seen > offline_after

        if should_be_offline and d.get("status") != "offline":
            await db.devices.update_one(
                {"_id": d["_id"]},
                {"$set": {"status": "offline", "updatedAt": now}},
            )

            if d.get("alertsEnabled", True):
                await _create_connectivity_alert_if_needed(
                    d["_id"], "Device appears offline (missed heartbeats)"
                )


async def run_forever(interval_seconds: int = DEFAULT_SWEEP_INTERVAL_SECONDS) -> None:
    """Run sweeps forever on a fixed interval."""
    while True:
        try:
            await sweep_once()
        except Exception as e:
            # Don't crash the loop in MVP; print for visibility.
            print(f"⚠️ Heartbeat sweep error: {e}")
        await asyncio.sleep(max(5, interval_seconds))


def start_background_sweep(interval_seconds: int = DEFAULT_SWEEP_INTERVAL_SECONDS) -> None:
    """Fire-and-forget background sweep task (call during app startup)."""
    asyncio.create_task(run_forever(interval_seconds=interval_seconds))

