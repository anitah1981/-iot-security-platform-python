# database.py - MongoDB Connection
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

# Global database connection
mongodb_client: Optional[AsyncIOMotorClient] = None
database = None

async def init_db(mongo_uri: str):
    """Connect to MongoDB"""
    global mongodb_client, database
    
    try:
        mongodb_client = AsyncIOMotorClient(mongo_uri)
        
        # Get database name from URI or use default
        # Use default database name for Atlas
        db_name = 'iot_security'
        database = mongodb_client[db_name]
        
        # Test connection
        await database.command('ping')
        print(f"✅ Connected to MongoDB: {db_name}")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        raise

async def close_db():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("✅ MongoDB connection closed")

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
    await database.devices.create_index("ipAddress", unique=True)
    await database.devices.create_index("status")
    await database.devices.create_index("lastSeen")
    
    # Alerts collection
    await database.alerts.create_index("deviceId")
    await database.alerts.create_index("createdAt")

    # Notification preferences
    await database.notification_preferences.create_index("userId", unique=True)

    # Notification logs
    await database.notification_logs.create_index("alertId")
    await database.notification_logs.create_index("createdAt")
    
    print("✅ Database indexes created")