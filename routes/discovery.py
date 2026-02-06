"""
Discovery API – device agent posts devices found on the network; app fetches them for "Discover devices".
POST /api/discovery: agent sends list (X-API-Key). GET /api/discovery: user gets last discovery (JWT).
"""
from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

from database import get_database
from models import DiscoveryPayload, DiscoveryResponse, DiscoveryDeviceItem
from routes.auth import get_current_user
from services.device_agent_key_service import get_user_by_api_key

router = APIRouter()

DISCOVERY_TTL_HOURS = 24  # Consider discovery stale after 24h


async def _discovery_api_key_user(request: Request) -> Optional[dict]:
    raw = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not raw:
        return None
    return await get_user_by_api_key(raw)


@router.post("/", response_model=DiscoveryResponse)
async def post_discovery(
    payload: DiscoveryPayload,
    request: Request,
    api_key_user: Optional[dict] = Depends(_discovery_api_key_user),
):
    """
    Device agent posts devices found on the network. Requires device agent API key (X-API-Key).
    """
    if not api_key_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key required (device agent API key from Settings)",
        )
    db = await get_database()
    user_id = api_key_user["_id"] if isinstance(api_key_user["_id"], ObjectId) else ObjectId(api_key_user["_id"])
    devices = [{"ip": d.ip, "hostname": d.hostname, "mac": d.mac} for d in payload.devices]
    now = datetime.utcnow()
    await db.discovery_results.update_one(
        {"userId": user_id},
        {"$set": {"devices": devices, "updatedAt": now}},
        upsert=True,
    )
    return DiscoveryResponse(
        devices=[DiscoveryDeviceItem(ip=d["ip"], hostname=d.get("hostname"), mac=d.get("mac")) for d in devices],
        updated_at=now,
    )


@router.get("/", response_model=DiscoveryResponse)
async def get_discovery(user: dict = Depends(get_current_user)):
    """
    Get the last discovery result for this user (devices found on your network by the device agent).
    """
    db = await get_database()
    user_id = user["_id"] if isinstance(user["_id"], ObjectId) else ObjectId(user["_id"])
    cutoff = datetime.utcnow() - timedelta(hours=DISCOVERY_TTL_HOURS)
    doc = await db.discovery_results.find_one(
        {"userId": user_id, "updatedAt": {"$gte": cutoff}},
    )
    if not doc:
        return DiscoveryResponse(devices=[], updated_at=None)
    devices = [
        DiscoveryDeviceItem(ip=d["ip"], hostname=d.get("hostname"), mac=d.get("mac"))
        for d in doc.get("devices", [])
    ]
    return DiscoveryResponse(devices=devices, updated_at=doc.get("updatedAt"))
