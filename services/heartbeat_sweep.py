"""
services/heartbeat_sweep.py - Background device heartbeat monitoring

Marks devices offline when heartbeats stop, so we detect network takeover,
DNS change, or device compromise quickly. Thresholds are security-focused:
short enough to catch real incidents, with optional per-device override.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId

from database import get_database


DEFAULT_SWEEP_INTERVAL_SECONDS = 20

# Security-focused: mark offline after 2 missed heartbeats (e.g. 30s interval → 60s).
# Minimum 30s so brief jitter doesn't false-trigger; use per-device offlineAfterSeconds for stricter.
OFFLINE_AFTER_MULTIPLIER = 2
OFFLINE_AFTER_MIN_SECONDS = 30
OFFLINE_AFTER_MAX_SECONDS = 90


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


def _offline_after_seconds(device: dict) -> int:
    """Seconds of no heartbeats before marking offline. Per-device override or security default."""
    explicit = device.get("offlineAfterSeconds")
    if explicit is not None and isinstance(explicit, (int, float)):
        return max(OFFLINE_AFTER_MIN_SECONDS, min(int(explicit), 300))
    interval = int(device.get("heartbeatInterval", 30))
    return max(OFFLINE_AFTER_MIN_SECONDS, min(OFFLINE_AFTER_MAX_SECONDS, interval * OFFLINE_AFTER_MULTIPLIER))


async def sweep_once() -> None:
    """
    One sweep: mark device offline if lastSeen is older than (2 × heartbeatInterval),
    min 30s, max 90s (or per-device offlineAfterSeconds). Fast enough to detect
    WiFi takeover / DNS change; avoids false positives from brief jitter.
    """
    db = await get_database()
    now = datetime.utcnow()

    cursor = db.devices.find({})
    devices = await cursor.to_list(length=None)

    for d in devices:
        last_seen: Optional[datetime] = d.get("lastSeen")

        if not last_seen:
            continue

        offline_after_sec = _offline_after_seconds(d)
        offline_after = timedelta(seconds=offline_after_sec)
        should_be_offline = now - last_seen > offline_after

        if should_be_offline and d.get("status") != "offline":
            # Require confirmed stale (one extra sweep cycle) before creating alert – CIA: integrity of alerts.
            # Reduces false positives from a single missed heartbeat or brief agent/server glitch.
            confirmed_stale = (now - last_seen).total_seconds() > (offline_after_sec + DEFAULT_SWEEP_INTERVAL_SECONDS)
            await db.devices.update_one(
                {"_id": d["_id"]},
                {"$set": {"status": "offline", "updatedAt": now}},
            )
            if d.get("alertsEnabled", True) and confirmed_stale:
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
            print(f"[WARNING] Heartbeat sweep error: {e}")
        await asyncio.sleep(max(5, interval_seconds))


def start_background_sweep(interval_seconds: int = DEFAULT_SWEEP_INTERVAL_SECONDS) -> None:
    """Fire-and-forget background sweep task (call during app startup)."""
    asyncio.create_task(run_forever(interval_seconds=interval_seconds))

