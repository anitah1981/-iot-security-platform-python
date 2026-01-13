"""
Payment Routes
Handles Stripe payment and subscription endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_database
from routes.auth import get_current_user
from services.stripe_service import StripeService

router = APIRouter(prefix="/api/payments", tags=["payments"])


class CheckoutRequest(BaseModel):
    plan: str  # "pro" or "business"


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_end: Optional[int] = None
    cancel_at_period_end: bool = False


@router.get("/plans")
async def get_plans():
    """
    Get all available subscription plans
    """
    plans = StripeService.get_all_plans()
    return {"plans": plans}


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: CheckoutRequest,
    user: dict = Depends(get_current_user)
):
    """
    Create a Stripe Checkout session for subscription
    
    - Validates plan selection
    - Creates Stripe checkout session
    - Returns checkout URL
    """
    plan_name = request.plan.lower()
    
    # Validate plan
    if plan_name not in ["pro", "business"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan. Choose 'pro' or 'business'"
        )
    
    # Check if user already has an active subscription
    if user.get("subscription_status") == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active subscription. Please manage it from your account settings."
        )
    
    try:
        # Create checkout session
        session = await StripeService.create_checkout_session(
            user_id=user["_id"],
            user_email=user["email"],
            plan_name=plan_name,
            success_url="http://localhost:8000/dashboard?payment=success",
            cancel_url="http://localhost:8000/pricing?payment=cancelled"
        )
        
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/subscription")
async def get_subscription(user: dict = Depends(get_current_user)):
    """
    Get current user's subscription details
    """
    subscription_id = user.get("subscription_id")
    
    if not subscription_id:
        return {
            "plan": user.get("plan", "free"),
            "status": "none",
            "message": "No active subscription"
        }
    
    try:
        subscription = await StripeService.get_subscription(subscription_id)
        
        if not subscription:
            return {
                "plan": user.get("plan", "free"),
                "status": "none",
                "message": "Subscription not found"
            }
        
        return {
            "plan": user.get("plan", "free"),
            "status": subscription["status"],
            "current_period_end": subscription["current_period_end"],
            "cancel_at_period_end": subscription["cancel_at_period_end"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/cancel-subscription")
async def cancel_subscription(user: dict = Depends(get_current_user)):
    """
    Cancel user's subscription at period end
    """
    subscription_id = user.get("subscription_id")
    
    if not subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found"
        )
    
    try:
        await StripeService.cancel_subscription(subscription_id)
        
        # Update user in database
        db = await get_database()
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "subscription_cancel_at_period_end": True,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        return {"message": "Subscription will be cancelled at the end of the billing period"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reactivate-subscription")
async def reactivate_subscription(user: dict = Depends(get_current_user)):
    """
    Reactivate a cancelled subscription
    """
    subscription_id = user.get("subscription_id")
    
    if not subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subscription found"
        )
    
    try:
        await StripeService.reactivate_subscription(subscription_id)
        
        # Update user in database
        db = await get_database()
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "subscription_cancel_at_period_end": False,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        return {"message": "Subscription reactivated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/customer-portal")
async def create_customer_portal_session(user: dict = Depends(get_current_user)):
    """
    Create a Stripe Customer Portal session
    Allows users to manage their subscription, payment methods, and invoices
    """
    customer_id = user.get("stripe_customer_id")
    
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer found. Please subscribe to a plan first."
        )
    
    try:
        session = await StripeService.create_customer_portal_session(
            customer_id=customer_id,
            return_url="http://localhost:8000/dashboard"
        )
        
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events
    
    Events handled:
    - checkout.session.completed: User completed payment
    - customer.subscription.updated: Subscription status changed
    - customer.subscription.deleted: Subscription cancelled
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    try:
        event = StripeService.verify_webhook_signature(payload, sig_header)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    db = await get_database()
    
    # Handle different event types
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        subscription_data = await StripeService.handle_checkout_completed(session)
        
        # Update user with subscription details
        await db.users.update_one(
            {"_id": subscription_data["user_id"]},
            {"$set": {
                "plan": subscription_data["plan"],
                "subscription_id": subscription_data["subscription_id"],
                "stripe_customer_id": subscription_data["customer_id"],
                "subscription_status": subscription_data["status"],
                "subscription_cancel_at_period_end": False,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        print(f"✅ Subscription activated for user {subscription_data['user_id']}: {subscription_data['plan']}")
    
    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        subscription_data = await StripeService.handle_subscription_updated(subscription)
        
        # Update subscription status
        await db.users.update_one(
            {"subscription_id": subscription_data["subscription_id"]},
            {"$set": {
                "subscription_status": subscription_data["status"],
                "subscription_cancel_at_period_end": subscription_data["cancel_at_period_end"],
                "updatedAt": datetime.utcnow()
            }}
        )
        
        print(f"✅ Subscription updated: {subscription_data['subscription_id']} - {subscription_data['status']}")
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        subscription_data = await StripeService.handle_subscription_deleted(subscription)
        
        # Downgrade user to free plan
        await db.users.update_one(
            {"subscription_id": subscription_data["subscription_id"]},
            {"$set": {
                "plan": "free",
                "subscription_status": "cancelled",
                "subscription_cancel_at_period_end": False,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        print(f"✅ Subscription cancelled: {subscription_data['subscription_id']}")
    
    return {"status": "success"}


@router.get("/usage")
async def get_usage(user: dict = Depends(get_current_user)):
    """
    Get user's current usage against their plan limits
    """
    db = await get_database()
    plan_name = user.get("plan", "free")
    plan_config = StripeService.get_plan_config(plan_name)
    
    if not plan_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid plan configuration"
        )
    
    # Count user's devices
    device_count = await db.devices.count_documents({"userId": user["_id"]})
    
    # Count alerts in retention period
    from datetime import timedelta
    retention_date = datetime.utcnow() - timedelta(days=plan_config["history_days"])
    alert_count = await db.alerts.count_documents({
        "userId": user["_id"],
        "createdAt": {"$gte": retention_date}
    })
    
    device_limit = plan_config["device_limit"]
    
    return {
        "plan": plan_name,
        "usage": {
            "devices": {
                "current": device_count,
                "limit": device_limit if device_limit > 0 else "unlimited",
                "percentage": (device_count / device_limit * 100) if device_limit > 0 else 0
            },
            "alerts": {
                "current": alert_count,
                "retention_days": plan_config["history_days"]
            }
        },
        "features": plan_config["features"]
    }
