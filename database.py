# database.py - MongoDB Connection
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from urllib.parse import urlparse

# Global database connection
mongodb_client: Optional[AsyncIOMotorClient] = None
database = None

def _db_name_from_uri(mongo_uri: str) -> str:
    """Parse database name from MONGO_URI; fallback to iot_security."""
    try:
        parsed = urlparse(mongo_uri)
        if parsed.scheme not in ("mongodb", "mongodb+srv"):
            return "iot_security"
        path = (parsed.path or "").strip("/")
        if path:
            # path can be "dbname" or "dbname?options"
            name = path.split("?")[0].strip("/") or "iot_security"
            return name
    except Exception:
        pass
    return "iot_security"

async def init_db(mongo_uri: str):
    """Connect to MongoDB"""
    global mongodb_client, database

    try:
        mongodb_client = AsyncIOMotorClient(mongo_uri)
        db_name = _db_name_from_uri(mongo_uri)
        database = mongodb_client[db_name]
        
        # Test connection
        await database.command('ping')
        print(f"Connected to MongoDB: {db_name}")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        raise

async def close_db():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("MongoDB connection closed")

async def get_database():
    """Get database instance"""
    if database is None:
        raise RuntimeError("Database not initialized")
    return database

async def create_indexes():
    """Create database indexes for performance"""
    
    # Users collection
    await database.users.create_index("email", unique=True)	
    
    # Devices collection
    # NOTE: device documents use camelCase keys (deviceId, ipAddress, lastSeen)
    await database.devices.create_index("deviceId", unique=True)
    await database.devices.create_index("ipAddress")
    await database.devices.create_index("status")
    await database.devices.create_index("lastSeen")
    
    # Alerts collection
    await database.alerts.create_index("deviceId")
    await database.alerts.create_index("createdAt")

    # Refresh tokens / sessions
    try:
        await database.refresh_tokens.create_index("token_hash")
        await database.refresh_tokens.create_index([("user_id", 1), ("revoked", 1)])
        await database.refresh_tokens.create_index("session_public_id")
        await database.refresh_tokens.create_index("expires_at")
    except Exception as e:
        print(f"[DB] refresh_tokens indexes: {e}")
    
    print("Database indexes created")