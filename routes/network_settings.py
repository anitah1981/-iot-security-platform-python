# routes/network_settings.py - Network Configuration (Router IP, etc.)
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from datetime import datetime

from database import get_database
from routes.auth import get_current_user

router = APIRouter()


class NetworkSettings(BaseModel):
    router_ip: Optional[str] = Field(None, description="Router/Gateway IP address (e.g., 192.168.1.1)")
    network_prefix: Optional[str] = Field(None, description="Network prefix (e.g., 192.168.1) - auto-detected from router IP")


class NetworkSettingsResponse(NetworkSettings):
    user_id: str
    updated_at: datetime


@router.get("/", response_model=NetworkSettingsResponse)
async def get_network_settings(current_user: dict = Depends(get_current_user)):
    """Get user's network settings (router IP)"""
    db = await get_database()
    user_id = ObjectId(current_user["_id"])
    
    settings = await db.network_settings.find_one({"userId": user_id})
    
    if not settings:
        return NetworkSettingsResponse(
            user_id=str(user_id),
            router_ip=None,
            network_prefix=None,
            updated_at=datetime.utcnow()
        )
    
    return NetworkSettingsResponse(
        user_id=str(user_id),
        router_ip=settings.get("routerIp"),
        network_prefix=settings.get("networkPrefix"),
        updated_at=settings.get("updatedAt", datetime.utcnow())
    )


@router.put("/", response_model=NetworkSettingsResponse)
async def update_network_settings(
    settings: NetworkSettings,
    current_user: dict = Depends(get_current_user)
):
    """Update network settings (router IP)"""
    db = await get_database()
    user_id = ObjectId(current_user["_id"])
    
    # Auto-detect network prefix from router IP
    network_prefix = None
    if settings.router_ip:
        try:
            ip_parts = settings.router_ip.split('.')
            if len(ip_parts) == 4:
                network_prefix = '.'.join(ip_parts[:3])
        except:
            pass
    
    settings_doc = {
        "userId": user_id,
        "routerIp": settings.router_ip,
        "networkPrefix": network_prefix,
        "updatedAt": datetime.utcnow()
    }
    
    await db.network_settings.update_one(
        {"userId": user_id},
        {"$set": settings_doc},
        upsert=True
    )
    
    return NetworkSettingsResponse(
        user_id=str(user_id),
        router_ip=settings.router_ip,
        network_prefix=network_prefix,
        updated_at=settings_doc["updatedAt"]
    )
