"""
Remove a user (and related signup data) so you can sign up again with the same email.
Use for demos/artefacts when signup already ran once.

Usage:
  python delete_user_by_email.py you@example.com

Requires MONGO_URI in .env (same as the app).
"""
import asyncio
import os
import sys
from urllib.parse import urlparse

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()


def _db_name_from_uri(mongo_uri: str) -> str:
    try:
        parsed = urlparse(mongo_uri)
        if parsed.scheme not in ("mongodb", "mongodb+srv"):
            return "iot_security"
        path = (parsed.path or "").strip("/")
        if path:
            return path.split("?")[0].strip("/") or "iot_security"
    except Exception:
        pass
    return "iot_security"


async def delete_user_by_email(email: str) -> None:
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("MONGO_URI not set. Set it in .env or export it.")
        sys.exit(1)

    email = email.strip().lower()
    client = AsyncIOMotorClient(mongo_uri)
    db_name = _db_name_from_uri(mongo_uri)
    db = client[db_name]

    user = await db.users.find_one({"email": email})
    if not user:
        print(f"No user found with email: {email}")
        client.close()
        return

    uid = user["_id"]
    uid_str = str(uid)

    # Signup creates these; remove so re-signup is clean
    prefs = await db.notification_preferences.delete_many({"userId": uid})
    tokens = await db.refresh_tokens.delete_many({"user_id": uid_str})
    deleted = await db.users.delete_one({"_id": uid})

    if deleted.deleted_count:
        print(f"Removed user: {email}")
        print(f"  notification_preferences deleted: {prefs.deleted_count}")
        print(f"  refresh_tokens deleted: {tokens.deleted_count}")
        print("You can sign up again with this email.")
    else:
        print("User found but delete failed (unexpected).")

    client.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_user_by_email.py <email>")
        sys.exit(1)
    asyncio.run(delete_user_by_email(sys.argv[1]))
