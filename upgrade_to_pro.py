"""
Direct Password Reset (No interaction required)
Resets password for anitah1981@gmail.com to Test123!!Test
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bcrypt import hashpw, gensalt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def reset_password():
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.iot_security
    
    # User details
    email = "anitah1981@gmail.com"
    new_password = "Test123!!Test"
    
    # Hash password
    password_hash = hashpw(new_password.encode('utf-8'), gensalt())
    
    # Update in database
    result = await db.users.update_one(
        {"email": email},
        {"$set": {"password": password_hash.decode('utf-8')}}
    )
    
    if result.matched_count > 0:
        print(f"✓ Password reset successful for {email}")
        print(f"  New password: {new_password}")
    else:
        print(f"✗ User not found: {email}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_password())
