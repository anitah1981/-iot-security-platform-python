"""
Alert Retention Cleanup Service
Automatically cleans up old alerts based on user's plan retention period
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict

from database import get_database
from services.stripe_service import StripeService


async def cleanup_old_alerts_for_all_users():
    """
    Clean up old alerts for all users based on their plan retention
    
    This should be run periodically (e.g., daily) as a background task
    """
    db = await get_database()
    
    # Get all users
    users = await db.users.find({}).to_list(length=None)
    
    total_deleted = 0
    users_processed = 0
    
    for user in users:
        try:
            plan_name = user.get("plan", "free")
            plan_config = StripeService.get_plan_config(plan_name)
            
            if not plan_config:
                continue
            
            retention_days = plan_config["history_days"]
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete old alerts for this user
            result = await db.alerts.delete_many({
                "userId": user["_id"],
                "createdAt": {"$lt": cutoff_date}
            })
            
            if result.deleted_count > 0:
                print(f"🗑️  Cleaned up {result.deleted_count} old alerts for user {user.get('email')} ({plan_name} plan, {retention_days} days retention)")
                total_deleted += result.deleted_count
            
            users_processed += 1
            
        except Exception as e:
            print(f"❌ Error cleaning up alerts for user {user.get('email')}: {e}")
            continue
    
    print(f"✅ Alert cleanup complete: {total_deleted} alerts deleted for {users_processed} users")
    return {"deleted": total_deleted, "users_processed": users_processed}


async def cleanup_old_alerts_for_user(user_id: str) -> int:
    """
    Clean up old alerts for a specific user
    
    Args:
        user_id: User's database ID
        
    Returns:
        Number of alerts deleted
    """
    db = await get_database()
    
    # Get user
    user = await db.users.find_one({"_id": user_id})
    if not user:
        return 0
    
    plan_name = user.get("plan", "free")
    plan_config = StripeService.get_plan_config(plan_name)
    
    if not plan_config:
        return 0
    
    retention_days = plan_config["history_days"]
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    # Delete old alerts
    result = await db.alerts.delete_many({
        "userId": user_id,
        "createdAt": {"$lt": cutoff_date}
    })
    
    return result.deleted_count


def start_retention_cleanup_task():
    """
    Start the background task for alert retention cleanup
    Runs daily at 2 AM UTC
    """
    async def cleanup_loop():
        while True:
            try:
                # Calculate time until next 2 AM UTC
                now = datetime.utcnow()
                next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
                
                # If it's past 2 AM today, schedule for tomorrow
                if now.hour >= 2:
                    next_run += timedelta(days=1)
                
                # Wait until next run
                wait_seconds = (next_run - now).total_seconds()
                print(f"📅 Next alert retention cleanup scheduled for {next_run.strftime('%Y-%m-%d %H:%M:%S')} UTC ({wait_seconds/3600:.1f} hours)")
                
                await asyncio.sleep(wait_seconds)
                
                # Run cleanup
                print(f"🧹 Starting scheduled alert retention cleanup...")
                await cleanup_old_alerts_for_all_users()
                
            except Exception as e:
                print(f"❌ Error in retention cleanup loop: {e}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)
    
    # Start the background task
    asyncio.create_task(cleanup_loop())
    print("✅ Alert retention cleanup task started")
