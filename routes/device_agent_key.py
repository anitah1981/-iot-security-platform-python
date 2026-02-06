"""
Device Agent API Key – allow users to generate/regenerate an API key for the device agent.
The key is used in X-API-Key header when sending heartbeats so devices are associated with their account.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from bson import ObjectId

from database import get_database
from routes.auth import get_current_user
from services.device_agent_key_service import generate_key

router = APIRouter()


class DeviceAgentKeyResponse(BaseModel):
    has_key: bool
    key_prefix: str | None = None  # Last 4 chars for display, e.g. "a1b2"


class DeviceAgentKeyRegenerateResponse(BaseModel):
    key: str  # Shown only once
    key_prefix: str


@router.get("/", response_model=DeviceAgentKeyResponse)
async def get_device_agent_key(user: dict = Depends(get_current_user)):
    """
    Get device agent API key status (masked). Use regenerate to get a new key or see it once.
    """
    return DeviceAgentKeyResponse(
        has_key=bool(user.get("device_agent_api_key_hash")),
        key_prefix=user.get("device_agent_api_key_prefix"),
    )


@router.post("/regenerate", response_model=DeviceAgentKeyRegenerateResponse)
async def regenerate_device_agent_key(user: dict = Depends(get_current_user)):
    """
    Generate a new device agent API key. The full key is returned only once; store it securely.
    Any previous key is invalidated. Use this key in the device agent config and in X-API-Key header for heartbeats.
    """
    db = await get_database()
    raw_key, key_hash, key_prefix = generate_key()
    user_id = user["_id"] if isinstance(user["_id"], ObjectId) else ObjectId(user["_id"])
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"device_agent_api_key_hash": key_hash, "device_agent_api_key_prefix": key_prefix}},
    )
    return DeviceAgentKeyRegenerateResponse(key=raw_key, key_prefix=key_prefix)
