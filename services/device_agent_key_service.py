"""
Device Agent API Key service – generate, verify, and resolve API keys for heartbeat/agent auth.
Keys are stored hashed (SHA-256) in users collection; raw key shown only once on generate/regenerate.
"""
import hashlib
import secrets
from typing import Optional, Tuple

from bson import ObjectId
from database import get_database


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _prefix(raw_key: str, length: int = 4) -> str:
    if len(raw_key) <= length:
        return raw_key
    return raw_key[-length:] if length > 0 else ""


def generate_key() -> Tuple[str, str, str]:
    """
    Generate a new device agent API key.
    Returns (raw_key, key_hash, key_prefix). Store hash and prefix; show raw_key only once.
    """
    raw = secrets.token_urlsafe(32)
    return raw, _hash_key(raw), _prefix(raw)


def verify_key(raw_key: str, stored_hash: str) -> bool:
    """Verify a raw key against stored hash."""
    if not raw_key or not stored_hash:
        return False
    return _hash_key(raw_key) == stored_hash


async def get_user_by_api_key(raw_key: str) -> Optional[dict]:
    """
    Validate API key and return user document (including _id) and family_id if in a family.
    Returns None if key invalid or user not found.
    """
    if not raw_key or len(raw_key) < 16:
        return None
    db = await get_database()
    stored_hash = _hash_key(raw_key)
    user = await db.users.find_one({"device_agent_api_key_hash": stored_hash})
    if not user:
        return None
    # Attach family_id for device ownership
    membership = await db.family_members.find_one({"user_id": user["_id"]})
    family_id = membership["family_id"] if membership and membership.get("family_id") else None
    user["_family_id"] = family_id
    return user
