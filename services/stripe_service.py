"""
Stripe Payment Service
Handles all Stripe-related operations for subscription management
"""

import stripe
import os
from typing import Optional, Dict, Any
from datetime import datetime

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Plan configurations
PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "currency": "gbp",
        "interval": "month",
        "device_limit": 5,
        "history_days": 30,
        "features": [
            "Up to 5 devices",
            "30-day alert history",
            "Email notifications",
            "Basic dashboard",
            "Community support"
        ],
        "stripe_price_id": None  # Free plan has no Stripe price
    },
    "pro": {
        "name": "Pro",
        "price": 4.99,
        "currency": "gbp",
        "interval": "month",
        "device_limit": 25,
        "history_days": 90,
        "features": [
            "Up to 25 devices",
            "90-day alert history",
            "Email + SMS + WhatsApp notifications",
            "Advanced dashboard with charts",
            "Alert exports (PDF/CSV)",
            "Priority email support",
            "Custom device grouping"
        ],
        "stripe_price_id": os.getenv("STRIPE_PRICE_PRO")
    },
    "business": {
        "name": "Business",
        "price": 9.99,
        "currency": "gbp",
        "interval": "month",
        "device_limit": -1,  # Unlimited
        "history_days": 365,
        "features": [
            "Unlimited devices",
            "1-year alert history",
            "All notification channels",
            "Advanced analytics & insights",
            "Alert exports with scheduling",
            "Multi-user teams & RBAC",
            "Audit logs & compliance",
            "Incident timeline & playbooks",
            "API access",
            "Priority phone support",
            "SLA guarantee"
        ],
        "stripe_price_id": os.getenv("STRIPE_PRICE_BUSINESS")
    }
}


class StripeService:
    """Service for handling Stripe operations"""
    
    @staticmethod
    def get_plan_config(plan_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific plan"""
        return PLANS.get(plan_name.lower())
    
    @staticmethod
    def get_all_plans() -> Dict[str, Dict[str, Any]]:
        """Get all available plans"""
        return PLANS
    
    @staticmethod
    async def create_checkout_session(
        user_id: str,
        user_email: str,
        plan_name: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for subscription
        
        Args:
            user_id: User's database ID
            user_email: User's email
            plan_name: Plan to subscribe to (pro/business)
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            
        Returns:
            Dict with checkout session details
        """
        plan = PLANS.get(plan_name.lower())
        if not plan or not plan.get("stripe_price_id"):
            raise ValueError(f"Invalid plan: {plan_name}")
        
        try:
            session = stripe.checkout.Session.create(
                customer_email=user_email,
                client_reference_id=user_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": plan["stripe_price_id"],
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "plan": plan_name.lower()
                },
                subscription_data={
                    "metadata": {
                        "user_id": user_id,
                        "plan": plan_name.lower()
                    }
                }
            )
            
            return {
                "session_id": session.id,
                "url": session.url
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    async def create_customer_portal_session(
        customer_id: str,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe Customer Portal session for managing subscription
        
        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session
            
        Returns:
            Dict with portal session URL
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return {
                "url": session.url
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    async def cancel_subscription(subscription_id: str) -> bool:
        """
        Cancel a subscription at period end
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            True if successful
        """
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return True
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    async def reactivate_subscription(subscription_id: str) -> bool:
        """
        Reactivate a cancelled subscription
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            True if successful
        """
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return True
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    async def get_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription details from Stripe
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription details or None
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "customer": subscription.customer,
                "plan": subscription["items"]["data"][0]["price"]["id"]
            }
        except stripe.error.StripeError:
            return None
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header
            
        Returns:
            Parsed event object
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise Exception("Invalid signature")
    
    @staticmethod
    async def handle_checkout_completed(session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful checkout completion
        
        Args:
            session: Stripe checkout session object
            
        Returns:
            Dict with user_id, subscription_id, customer_id, plan
        """
        user_id = session.get("client_reference_id") or session["metadata"].get("user_id")
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")
        plan = session["metadata"].get("plan", "pro")
        
        return {
            "user_id": user_id,
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "plan": plan,
            "status": "active"
        }
    
    @staticmethod
    async def handle_subscription_updated(subscription: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle subscription update event
        
        Args:
            subscription: Stripe subscription object
            
        Returns:
            Dict with subscription details
        """
        return {
            "subscription_id": subscription["id"],
            "status": subscription["status"],
            "current_period_end": subscription["current_period_end"],
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
            "plan": subscription["items"]["data"][0]["price"]["id"]
        }
    
    @staticmethod
    async def handle_subscription_deleted(subscription: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle subscription deletion event
        
        Args:
            subscription: Stripe subscription object
            
        Returns:
            Dict with subscription_id
        """
        return {
            "subscription_id": subscription["id"],
            "status": "cancelled"
        }
