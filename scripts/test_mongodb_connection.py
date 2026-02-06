#!/usr/bin/env python3
"""
Test MongoDB Atlas connection - run this to verify your MONGO_URI works.
Usage: python scripts/test_mongodb_connection.py
Or set MONGO_URI env var: MONGO_URI=your-connection-string python scripts/test_mongodb_connection.py
"""
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test_connection():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("Set MONGO_URI environment variable:")
        print()
        print("PowerShell (Windows):")
        print('  $env:MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net/iot_security?retryWrites=true&w=majority"')
        print("  python scripts\\test_mongodb_connection.py")
        print()
        print("Or edit this script and set mongo_uri directly (not recommended for production).")
        sys.exit(1)
    
    print(f"Testing connection to: {mongo_uri.split('@')[1] if '@' in mongo_uri else mongo_uri[:50]}...")
    print()
    
    try:
        client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        print("✓ Connection successful!")
        print()
        
        # List databases
        db_list = await client.list_database_names()
        print(f"Databases: {', '.join(db_list) if db_list else '(none yet)'}")
        
        # Check if iot_security exists
        db = client.iot_security
        collections = await db.list_collection_names()
        print(f"Collections in 'iot_security': {', '.join(collections) if collections else '(none yet - will be created on first use)'}")
        print()
        print("✓ MongoDB Atlas is ready for deployment!")
        print("Copy your MONGO_URI to Railway/Render environment variables.")
        
        client.close()
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print()
        print("Check:")
        print("  1. Your connection string includes the correct password")
        print("  2. Network Access allows 0.0.0.0/0 (or your host IP)")
        print("  3. Database user exists and has permissions")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection())
